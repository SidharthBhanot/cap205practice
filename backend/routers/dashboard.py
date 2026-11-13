from collections import Counter
from dataclasses import asdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..constants import OPEN_STATUSES
from ..dependencies import get_db
from ..models import AppState, Conflict, Course, Obligation, Source
from ..reconciliation import normalize_title
from ..serializers import conflict_json, obligation_json, timestamp

router = APIRouter()


@router.get("/dashboard", tags=["Dashboard"])
def dashboard(request: Request, db: Session = Depends(get_db)):
    records = list(db.scalars(select(Obligation).options(joinedload(Obligation.course), joinedload(Obligation.source)).order_by(Obligation.recorded_at.desc(), Obligation.id.desc())))
    issues = list(db.scalars(select(Conflict).where(Conflict.is_current.is_(True)).order_by(Conflict.id)))
    open_issues = [i for i in issues if i.status in OPEN_STATUSES or i.evidence_changed]
    incomplete = [r for r in records if not normalize_title(r.title) or r.course_id is None or not r.obligation_type or r.obligation_type == "Other" or r.deadline is None]
    state = db.get(AppState, 1)
    return {"total_obligations": len(records), "total_sources": db.scalar(select(func.count()).select_from(Source)),
            "total_courses": db.scalar(select(func.count()).select_from(Course)),
            "potential_duplicates": sum(i.conflict_type == "DUPLICATE" for i in open_issues),
            "unresolved_conflicts": sum(i.conflict_type == "DEADLINE_CONFLICT" or (i.conflict_type == "INCOMPLETE_INFORMATION" and len(i.record_ids) > 1) for i in open_issues),
            "incomplete_records": len(incomplete), "issues_needing_attention": len(open_issues),
            "recent_obligations": [obligation_json(r) for r in records[:5]],
            "priority_issues": [conflict_json(i) for i in sorted(open_issues, key=lambda i: i.conflict_type != "DEADLINE_CONFLICT")[:4]],
            "issue_breakdown": dict(Counter(i.conflict_type for i in issues)),
            "is_stale": state.data_revision != state.reconciled_revision or state.last_config != asdict(request.app.state.rule_config),
            "synthetic_data": state.synthetic_data, "last_reconciled_at": timestamp(state.last_reconciled_at),
            "summary": state.run_summary}
