"""Per-record and cross-record issue detection; never chooses a winning source."""
from datetime import datetime, timedelta

from .constants import IssueType
from .database import utcnow
from .reconciliation import RuleConfig, field, normalize_title


def detect_issues(records, comparisons, config=None, now=None):
    config, now = config or RuleConfig(), now or utcnow()
    issues = []

    def add(kind, ids, explanation):
        ids = sorted(ids)
        issues.append({"fingerprint": f"{kind.value}:" + ":".join(map(str, ids)),
                       "conflict_type": kind.value, "record_ids": ids, "explanation": explanation})

    for record in records:
        identifier = field(record, "id")
        if field(record, "deadline") is None:
            add(IssueType.MISSING, [identifier], "No deadline was recorded. Check the original source; no due date has been inferred.")
        missing = []
        if field(record, "course_id") is None:
            missing.append("course")
        if not normalize_title(field(record, "title")):
            missing.append("title")
        if not field(record, "obligation_type") or field(record, "obligation_type") == "Other":
            missing.append("specific obligation type")
        if missing:
            add(IssueType.INCOMPLETE, [identifier], "Missing or unspecified " + ", ".join(missing) + ". Verify the source before relying on this record.")
        updated = field(record, "updated_at")
        checked = field(field(record, "source"), "last_checked_at")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated.replace("Z", "+00:00")).replace(tzinfo=None)
        if isinstance(checked, str):
            checked = datetime.fromisoformat(checked.replace("Z", "+00:00")).replace(tzinfo=None)
        last_verified = max(filter(None, [updated, checked]), default=now)
        if field(record, "status") not in ("Completed", "Cancelled") and last_verified < now - timedelta(days=config.stale_days):
            add(IssueType.OUTDATED, [identifier], f"Neither this active record nor its source has been updated or checked in {config.stale_days} days. It may be outdated; age alone does not prove it incorrect.")
    for comparison in comparisons:
        ids = [comparison["obligation_a_id"], comparison["obligation_b_id"]]
        classification = comparison["classification"]
        if classification == "CONFLICT":
            if "deadline" in comparison["conflicting_fields"]:
                add(IssueType.DEADLINE, ids, comparison["reason"])
            if "obligation_type" in comparison["conflicting_fields"]:
                add(IssueType.INCOMPLETE, ids, "The likely same obligation has inconsistent type information. " + comparison["reason"])
        elif classification in ("MATCH", "POTENTIAL_MATCH"):
            prefix = "Likely duplicate. " if classification == "MATCH" else "Possible duplicate; identity is uncertain. "
            add(IssueType.DUPLICATE, ids, prefix + comparison["reason"])
    return issues
