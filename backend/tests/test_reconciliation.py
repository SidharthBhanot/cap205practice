from datetime import date, datetime, timedelta

import pytest

from backend.reconciliation import (
    RuleConfig, calculate_title_similarity, compare_obligations,
    normalize_title, reconcile_obligations,
)
from backend.validation import detect_issues


def record(identifier=1, **changes):
    return {"id": identifier, "course_id": 1, "title": "Assignment 2",
            "obligation_type": "Assignment", "deadline": date(2026, 10, 20),
            "source_id": identifier, "status": "Planned", **changes}


@pytest.mark.parametrize("value,expected", [
    ("  Assignment-02!! ", "assignment 2"), ("ASSIGNMENT\t2\n", "assignment 2"),
    ("Ａｓｓｉｇｎｍｅｎｔ ２", "assignment 2"), ("Graph_theory: Quiz", "graph theory quiz"),
    ("", ""), (None, ""), ("!!!", ""), ("Café résumé", "café résumé"),
])
def test_normalization(value, expected):
    assert normalize_title(value) == expected


def test_similarity_is_bounded_symmetric_and_transparent():
    assert calculate_title_similarity("Quiz-1", " quiz 01! ") == 1
    assert calculate_title_similarity("", "") == 0
    for a, b in [("Project proposal", "Project proposal draft"), ("tide", "diet"), ("alpha", "zzz")]:
        score = calculate_title_similarity(a, b)
        assert 0 <= score <= 1
        assert score == calculate_title_similarity(b, a)
    assert calculate_title_similarity("project proposal", "project proposal draft") > .62


def test_match_preserves_original_records():
    a, b = record(), record(2, title="  ASSIGNMENT-02! ")
    before = b.copy()
    result = compare_obligations(a, b)
    assert result["classification"] == "MATCH"
    assert result["reason"] and b == before


def test_deadline_conflict_never_picks_a_winner():
    result = compare_obligations(record(), record(2, deadline=date(2026, 10, 22)))
    assert result["classification"] == "CONFLICT"
    assert result["conflicting_fields"] == ["deadline"]
    assert "neither is assumed correct" in result["reason"]


@pytest.mark.parametrize("changes", [
    {"deadline": None}, {"course_id": None}, {"obligation_type": None},
    {"obligation_type": "Other"}, {"title": "Assignment"},
])
def test_missing_evidence_is_potential_not_conflict(changes):
    assert compare_obligations(record(), record(2, **changes))["classification"] == "POTENTIAL_MATCH"


def test_two_missing_deadlines_are_not_a_confident_match():
    result = compare_obligations(record(deadline=None), record(2, deadline=None))
    assert result["classification"] == "POTENTIAL_MATCH"
    assert "uncertainty" in result["reason"]


@pytest.mark.parametrize("changes", [{"course_id": 2}, {"title": "Assignment 3"}, {"title": "Graph theory final"}])
def test_unrelated(changes):
    assert compare_obligations(record(), record(2, **changes))["classification"] == "UNRELATED"


def test_generic_titles_cannot_establish_identity():
    assert compare_obligations(record(title="Assignment"), record(2, title="Assignment"))["classification"] == "POTENTIAL_MATCH"


def test_type_conflict_is_explained_and_detected():
    records = [record(), record(2, obligation_type="Quiz")]
    result = compare_obligations(*records)
    assert result["classification"] == "CONFLICT"
    assert "obligation_type" in result["conflicting_fields"]
    issues = detect_issues(records, [result])
    assert issues[0]["conflict_type"] == "INCOMPLETE_INFORMATION"


def test_fuzzy_identity_cannot_make_deadline_conflict():
    a = record(title="Project proposal", obligation_type="Project")
    b = record(2, title="Project proposal draft", obligation_type="Project", deadline=date(2026, 10, 25))
    assert compare_obligations(a, b)["classification"] == "POTENTIAL_MATCH"


def test_same_source_exact_duplicates_are_still_detected():
    assert compare_obligations(record(), record(2, source_id=1))["classification"] == "MATCH"


def test_thresholds_change_classification_without_bypassing_other_evidence():
    a, b = record(title="Project proposal"), record(2, title="Project proposal draft")
    assert compare_obligations(a, b, RuleConfig(.9, .62))["classification"] == "POTENTIAL_MATCH"
    assert compare_obligations(a, b, RuleConfig(.7, .5))["classification"] == "MATCH"
    assert compare_obligations(a, {**b, "course_id": 9}, RuleConfig(.7, .5))["classification"] == "UNRELATED"


@pytest.mark.parametrize("args", [(1.1,.5),(.5,.8),(.5,.5),(.9,-.1),(float('nan'),.2),(.9,.6,0)])
def test_invalid_thresholds_fail_fast(args):
    with pytest.raises(ValueError):
        RuleConfig(*args)


def test_blocking_skips_distinct_records_but_checks_cross_course_title_collision():
    records = [record(), record(2, course_id=2), record(3, title="Graph theory examination"),
               record(4, title="", course_id=None)]
    result = reconcile_obligations(records)
    assert result["possible_pairs"] == 6 and result["candidate_pairs"] == 1
    assert result["comparisons"][0]["classification"] == "UNRELATED"
    assert result == reconcile_obligations(list(reversed(records)))


def test_missing_and_incomplete_are_separate_issues():
    issues = detect_issues([record(deadline=None, title="", course_id=None, obligation_type=None)], [])
    assert {i["conflict_type"] for i in issues} == {"MISSING_DEADLINE", "INCOMPLETE_INFORMATION"}


def test_outdated_requires_age_not_just_overdue_and_respects_checked_source():
    now = datetime(2026, 10, 9)
    old = record(updated_at=now-timedelta(days=40), deadline=date(2026, 9, 1))
    assert detect_issues([old], [], now=now)[0]["conflict_type"] == "OUTDATED_INFORMATION"
    assert not detect_issues([{**old, "updated_at": now}], [], now=now)
    assert not detect_issues([{**old, "source": {"last_checked_at": now}}], [], now=now)
    assert not detect_issues([{**old, "status": "Completed"}], [], now=now)


def test_empty_and_duplicate_id_inputs():
    assert reconcile_obligations([])["comparisons"] == []
    with pytest.raises(ValueError):
        reconcile_obligations([record(), record()])
