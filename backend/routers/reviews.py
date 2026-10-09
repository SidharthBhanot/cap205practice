from dataclasses import asdict

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constants import Classification, IssueType, ReviewStatus
from ..database import utcnow
from ..dependencies import get_db, get_or_404
from ..models import AppState, Conflict, Obligation, ReconciliationResult
from ..schemas import ReviewUpdate
from ..serializers import conflict_json, obligation_json
from ..services import result_json, run_reconciliation

router = APIRouter()


@router.get("/conflicts", tags=["Issues"])
def conflicts(status: ReviewStatus | None = None, conflict_type: IssueType | None = None,
              current_only: bool = False, course_id: int | None = None,
              offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
              db: Session = Depends(get_db)):
    query = select(Conflict).order_by(Conflict.is_current.desc(), Conflict.detected_at.desc(), Conflict.id)
    if status:
        query = query.where(Conflict.status == status)
    if conflict_type:
        query = query.where(Conflict.conflict_type == conflict_type)
    if current_only:
        query = query.where(Conflict.is_current.is_(True))
    items = list(db.scalars(query))
    if course_id:
        items = [i for i in items if any(r["course_id"] == course_id for r in i.source_records)]
    return {"items": [conflict_json(i) for i in items[offset:offset + limit]], "total": len(items), "offset": offset, "limit": limit}


@router.get("/conflicts/{identifier}", tags=["Issues"])
def conflict(identifier: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Conflict, identifier)
    return {**conflict_json(item), "current_records": [obligation_json(o) for o in item.obligations]}


@router.put("/conflicts/{identifier}/status", tags=["Issues"])
def update_status(identifier: int, data: ReviewUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, Conflict, identifier)
    item.status = data.status.value
    item.resolution_notes = data.resolution_notes
    item.reviewed_at = utcnow()
    item.reviewed_evidence_hash = item.evidence_hash
    item.evidence_changed = False
    db.commit()
    return conflict_json(item)


@router.post("/reconcile", tags=["Reconciliation"])
def reconcile(request: Request, db: Session = Depends(get_db)):
    return run_reconciliation(db, request.app.state.rule_config)


@router.get("/reconciliation/config", tags=["Reconciliation"])
def configuration(request: Request):
    return {**asdict(request.app.state.rule_config),
            "similarity_method": "60% token Jaccard + 40% symmetric sorted-token character similarity",
            "blocking_method": "Same course and shared informative token, plus exact normalized-title collisions across courses",
            "deadline_precision": "Calendar dates; no time-of-day inference"}


@router.get("/reconciliation/results", tags=["Reconciliation"])
def results(request: Request, classification: Classification | None = None, course_id: int | None = None,
            issue_type: IssueType | None = None, offset: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    query = select(ReconciliationResult).order_by(ReconciliationResult.id)
    if classification:
        query = query.where(ReconciliationResult.classification == classification)
    items = list(db.scalars(query))
    issues = {i.id: i for i in db.scalars(select(Conflict))}
    if course_id:
        items = [r for r in items if any(o["course_id"] == course_id for o in r.source_records)]
    if issue_type:
        items = [r for r in items if any(i in issues and issues[i].conflict_type == issue_type for i in r.conflict_ids)]
    state = db.get(AppState, 1)
    stale = state.data_revision != state.reconciled_revision or state.last_config != asdict(request.app.state.rule_config)
    return {"items": [result_json(i, issues) for i in items[offset:offset + limit]], "total": len(items),
            "offset": offset, "limit": limit, "is_stale": stale, "summary": state.run_summary}
