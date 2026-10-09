import hashlib
import json
from collections import Counter

from sqlalchemy import delete, select, text
from sqlalchemy.orm import joinedload

from .database import utcnow
from .models import AppState, Conflict, Obligation, ReconciliationResult
from .reconciliation import RuleConfig, reconcile_obligations
from .serializers import conflict_json, obligation_json, timestamp
from .validation import detect_issues


def evidence_digest(snapshots):
    # Exclude incidental check/record timestamps. A changed deadline/title/type/
    # course/source/status or source description is substantive evidence.
    clean = []
    for record in snapshots:
        item = {k: v for k, v in record.items() if k not in ("recorded_at", "updated_at")}
        item["source"] = {k: v for k, v in item["source"].items()
                          if k not in ("recorded_at", "updated_at", "last_checked_at")}
        if item.get("course"):
            item["course"] = {k: v for k, v in item["course"].items() if k != "created_at"}
        clean.append(item)
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()


def run_reconciliation(db, config=None, now=None):
    """One transaction, stable issue fingerprints and no automatic resolutions.

    BEGIN IMMEDIATE serializes SQLite writers before reading the source snapshot.
    The caller supplies a fresh Session. A failed run rolls back atomically.
    """
    config, now = config or RuleConfig(), now or utcnow()
    db.execute(text("BEGIN IMMEDIATE"))
    records = list(db.scalars(select(Obligation).options(joinedload(Obligation.course), joinedload(Obligation.source)).order_by(Obligation.id)))
    by_id = {record.id: record for record in records}
    snapshots = {record.id: obligation_json(record) for record in records}
    report = reconcile_obligations(records, config)
    detected = detect_issues(records, report["comparisons"], config, now)
    existing = {issue.fingerprint: issue for issue in db.scalars(select(Conflict))}
    for issue in existing.values():
        issue.is_current = False
    created, changed = 0, 0
    current_issues = []
    for item in detected:
        evidence = [snapshots[i] for i in item["record_ids"]]
        digest = evidence_digest(evidence)
        issue = existing.get(item["fingerprint"])
        if issue is None:
            issue = Conflict(**item, detected_at=now, source_records=evidence, evidence_hash=digest)
            db.add(issue)
            created += 1
        else:
            changed += issue.evidence_hash != digest
            issue.explanation = item["explanation"]
            issue.source_records = evidence
            issue.evidence_hash = digest
        issue.obligations = [by_id[i] for i in item["record_ids"]]
        issue.last_detected_at = now
        issue.is_current = True
        issue.evidence_changed = bool(issue.reviewed_evidence_hash and issue.reviewed_evidence_hash != digest)
        current_issues.append(issue)
    db.flush()
    # Results are the latest run; issues retain stable IDs and review history.
    db.execute(delete(ReconciliationResult))
    for comparison in report["comparisons"]:
        a, b = comparison["obligation_a_id"], comparison["obligation_b_id"]
        related = [issue.id for issue in current_issues if set(issue.record_ids).issubset({a, b})]
        db.add(ReconciliationResult(obligation_a_id=a, obligation_b_id=b, pair_key=f"{a}:{b}",
               classification=comparison["classification"], title_similarity=comparison["title_similarity"],
               reason=comparison["reason"], source_records=[snapshots[a], snapshots[b]], conflict_ids=related,
               compared_at=now, course_id=by_id[a].course_id if by_id[a].course_id == by_id[b].course_id else None))
    counts = {name: 0 for name in ("MATCH", "POTENTIAL_MATCH", "CONFLICT", "UNRELATED")}
    counts.update(Counter(item["classification"] for item in report["comparisons"]))
    summary = {"candidate_pairs": report["candidate_pairs"], "possible_pairs": report["possible_pairs"],
               "skipped_pairs": report["skipped_pairs"], "classifications": counts,
               "new_issues": created, "changed_issues": changed, "current_issues": len(current_issues),
               "compared_at": timestamp(now), "config": report["config"]}
    state = db.get(AppState, 1)
    state.reconciled_revision = state.data_revision
    state.last_reconciled_at = now
    state.last_config = report["config"]
    state.run_summary = summary
    db.commit()
    return summary


def result_json(result, issues):
    related = [conflict_json(issues[i]) for i in result.conflict_ids if i in issues]
    statuses = [issue["status"] for issue in related]
    if any(i["evidence_changed"] for i in related):
        verification = "Needs Verification"
    elif "Needs Verification" in statuses:
        verification = "Needs Verification"
    elif "Under Review" in statuses:
        verification = "Under Review"
    elif statuses:
        verification = "Resolved" if "Resolved" in statuses else "Dismissed"
    else:
        verification = "Not required" if result.classification == "UNRELATED" else "Needs Verification"
    return {"id": result.id, "classification": result.classification,
            "title_similarity": result.title_similarity, "reason": result.reason,
            "source_records": result.source_records, "conflicts": related,
            "verification_status": verification, "compared_at": timestamp(result.compared_at)}
