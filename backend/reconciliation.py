"""Pure, deterministic rules. No database writes, network, AI or source ranking."""
import os
import re
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from itertools import combinations
from math import isfinite

from .constants import Classification as C

GENERIC_WORDS = {"assignment", "quiz", "examination", "exam", "project", "task", "homework",
                 "the", "a", "an", "of", "for", "and", "to", "in"}


@dataclass(frozen=True)
class RuleConfig:
    match_threshold: float = 0.90
    potential_threshold: float = 0.62
    stale_days: int = 30

    def __post_init__(self):
        if not all(isfinite(x) for x in (self.match_threshold, self.potential_threshold)):
            raise ValueError("Similarity thresholds must be finite.")
        if not 0 <= self.potential_threshold < self.match_threshold <= 1:
            raise ValueError("Require 0 <= potential threshold < match threshold <= 1.")
        if self.stale_days < 1:
            raise ValueError("STALE_DAYS must be at least 1.")

    @classmethod
    def from_env(cls):
        return cls(float(os.getenv("MATCH_THRESHOLD", "0.90")),
                   float(os.getenv("POTENTIAL_THRESHOLD", "0.62")),
                   int(os.getenv("STALE_DAYS", "30")))


def normalize_title(title):
    """Unicode NFKC + casefold + punctuation/whitespace + leading-zero numbers.

    The caller's source record is never changed. No semantic synonym guessing.
    """
    value = unicodedata.normalize("NFKC", title or "").casefold()
    value = "".join(ch if ch.isalnum() else " " for ch in value)
    value = re.sub(r"\b\d+\b", lambda m: str(int(m.group())), value)
    return " ".join(value.split())


def calculate_title_similarity(title_a, title_b):
    """60% token Jaccard + 40% symmetric character similarity on sorted tokens.

    Scores are evidence, not probabilities. Empty titles score 0, not 1.
    """
    a, b = normalize_title(title_a), normalize_title(title_b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    sa, sb = set(a.split()), set(b.split())
    jaccard = len(sa & sb) / len(sa | sb)
    aa, bb = " ".join(sorted(sa)), " ".join(sorted(sb))
    sequence = (SequenceMatcher(None, aa, bb, autojunk=False).ratio()
                + SequenceMatcher(None, bb, aa, autojunk=False).ratio()) / 2
    return round(0.6 * jaccard + 0.4 * sequence, 6)


def field(record, key, default=None):
    return record.get(key, default) if isinstance(record, dict) else getattr(record, key, default)


def compare_obligations(a, b, config=None):
    config = config or RuleConfig()
    ta, tb = normalize_title(field(a, "title")), normalize_title(field(b, "title"))
    score = calculate_title_similarity(ta, tb)
    result = {"obligation_a_id": field(a, "id"), "obligation_b_id": field(b, "id"),
              "title_similarity": score, "conflicting_fields": []}

    def conclude(classification, reason, fields=None):
        return {**result, "classification": classification.value, "reason": reason,
                "conflicting_fields": fields or []}

    ca, cb = field(a, "course_id"), field(b, "course_id")
    if ca is not None and cb is not None and ca != cb:
        return conclude(C.UNRELATED, "The course identities differ. Similar or identical titles do not establish the same obligation across courses.")
    if not ta or not tb:
        return conclude(C.POTENTIAL if ca is not None and ca == cb else C.UNRELATED,
                        "A title is missing. Available evidence cannot establish an obligation identity; verify the incomplete record.")
    na, nb = re.findall(r"\b\d+\b", ta), re.findall(r"\b\d+\b", tb)
    if na and nb and na != nb:
        return conclude(C.UNRELATED, "The numeric identifiers in the titles differ (for example, assignment 2 versus assignment 3).")
    if score < config.potential_threshold:
        return conclude(C.UNRELATED, f"Title similarity {score:.2f} is below the potential-match threshold {config.potential_threshold:.2f}.")
    if ca is None or cb is None:
        return conclude(C.POTENTIAL, "Titles are similar, but course identity is missing. Human verification is required.")
    if not (set(ta.split()) - GENERIC_WORDS) or not (set(tb.split()) - GENERIC_WORDS):
        return conclude(C.POTENTIAL, "The course agrees, but the titles are generic and lack a distinguishing topic or number.")
    if bool(na) != bool(nb):
        return conclude(C.POTENTIAL, "Only one title contains a numeric identifier. Verify the assignment identity before comparing deadlines.")
    if score < config.match_threshold:
        return conclude(C.POTENTIAL, f"The course agrees and title similarity is {score:.2f}, below the strong-match threshold {config.match_threshold:.2f}. Verify identity before treating differences as conflicts.")
    type_a, type_b = field(a, "obligation_type"), field(b, "obligation_type")
    if not type_a or not type_b or "Other" in (type_a, type_b):
        return conclude(C.POTENTIAL, "The course and titles agree, but the obligation type is missing or unspecified. Human verification is required.")
    different = []
    if type_a != type_b:
        different.append("obligation_type")
    da, db = field(a, "deadline"), field(b, "deadline")
    if da is not None and db is not None and str(da) != str(db):
        different.append("deadline")
    if different:
        labels = " and ".join("deadlines" if x == "deadline" else "obligation types" for x in different)
        return conclude(C.CONFLICT, f"The course and titles strongly agree, but the {labels} differ. Both source records are preserved; neither is assumed correct. Needs verification.", different)
    if da is None or db is None:
        return conclude(C.POTENTIAL, "The course, title and type agree, but at least one deadline is missing. This is uncertainty, not a deadline conflict.")
    same_source = field(a, "source_id") == field(b, "source_id")
    if same_source and ta != tb:
        return conclude(C.POTENTIAL, "Similar titles come from the same recorded source; independent corroboration is unavailable and the original titles differ.")
    source_text = "different recorded sources" if not same_source else "the same recorded source"
    return conclude(C.MATCH, f"Course, specific title, type and deadline agree in {source_text}. No material conflict was identified; a human can verify this possible duplicate.")


def candidate_pairs(records):
    """Block by course and informative tokens; audit identical-title collisions globally.

    This avoids most irrelevant pairs. Unknown-course records are only candidates
    on an exact normalized-title collision. Empty titles produce per-record issues.
    """
    postings, exact = defaultdict(list), defaultdict(list)
    by_id = {field(record, "id"): record for record in records}
    if len(by_id) != len(records) or None in by_id:
        raise ValueError("Reconciliation requires unique, non-null record IDs.")
    pairs = set()
    for identifier, record in by_id.items():
        title = normalize_title(field(record, "title"))
        if not title:
            continue
        exact[title].append(identifier)
        course = field(record, "course_id")
        if course is not None:
            for token in set(title.split()) - GENERIC_WORDS:
                postings[(course, token)].append(identifier)
    for bucket in list(postings.values()) + list(exact.values()):
        pairs.update(tuple(sorted(pair)) for pair in combinations(bucket, 2))
    return [(by_id[a], by_id[b]) for a, b in sorted(pairs)]


def reconcile_obligations(records, config=None):
    records = list(records)
    config = config or RuleConfig()
    pairs = candidate_pairs(records)
    comparisons = [compare_obligations(a, b, config) for a, b in pairs]
    return {"comparisons": comparisons, "candidate_pairs": len(pairs),
            "possible_pairs": len(records) * (len(records) - 1) // 2,
            "skipped_pairs": len(records) * (len(records) - 1) // 2 - len(pairs),
            "config": asdict(config)}
