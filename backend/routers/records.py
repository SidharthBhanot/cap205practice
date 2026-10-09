from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..constants import ObligationStatus, ObligationType, SourceType
from ..dependencies import get_db, get_or_404, touch_data
from ..models import Course, Obligation, Source
from ..schemas import CourseCreate, ObligationWrite, SourceWrite
from ..serializers import course_json, obligation_json, source_json

router = APIRouter()


@router.get("/courses", tags=["Courses"])
def courses(db: Session = Depends(get_db)):
    return [course_json(c) for c in db.scalars(select(Course).order_by(Course.code))]


@router.post("/courses", status_code=201, tags=["Courses"])
def create_course(data: CourseCreate, db: Session = Depends(get_db)):
    item = Course(**data.model_dump())
    db.add(item)
    touch_data(db)
    db.commit()
    return course_json(item)


@router.get("/sources", tags=["Sources"])
def sources(q: str = "", source_type: SourceType | None = None, db: Session = Depends(get_db)):
    query = select(Source).order_by(Source.name)
    if q.strip():
        query = query.where(Source.name.icontains(q.strip(), autoescape=True))
    if source_type:
        query = query.where(Source.source_type == source_type)
    counts = dict(db.execute(select(Obligation.source_id, func.count()).group_by(Obligation.source_id)).all())
    return [{**source_json(s), "obligation_count": counts.get(s.id, 0)} for s in db.scalars(query)]


@router.post("/sources", status_code=201, tags=["Sources"])
def create_source(data: SourceWrite, db: Session = Depends(get_db)):
    item = Source(**data.model_dump())
    db.add(item)
    touch_data(db)
    db.commit()
    return source_json(item)


@router.get("/sources/{identifier}", tags=["Sources"])
def source(identifier: int, db: Session = Depends(get_db)):
    return source_json(get_or_404(db, Source, identifier))


@router.put("/sources/{identifier}", tags=["Sources"])
def update_source(identifier: int, data: SourceWrite, db: Session = Depends(get_db)):
    item = get_or_404(db, Source, identifier)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    touch_data(db)
    db.commit()
    return source_json(item)


@router.delete("/sources/{identifier}", status_code=204, tags=["Sources"])
def delete_source(identifier: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Source, identifier)
    if db.scalar(select(func.count()).select_from(Obligation).where(Obligation.source_id == identifier)):
        raise HTTPException(409, "This source is used by obligations. Reassign or delete those records first.")
    db.delete(item)
    touch_data(db)
    db.commit()
    return Response(status_code=204)


@router.get("/obligations", tags=["Obligations"])
def obligations(
    q: str = Query("", max_length=240), course_id: int | None = None, source_id: int | None = None,
    obligation_type: ObligationType | None = None, status: ObligationStatus | None = None,
    deadline_from: date | None = None, deadline_to: date | None = None, missing_deadline: bool = False,
    sort_by: Literal["deadline", "title", "course", "type", "status", "recorded_at"] = "deadline",
    order: Literal["asc", "desc"] = "asc", offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    if deadline_from and deadline_to and deadline_from > deadline_to:
        raise HTTPException(422, "Deadline from must be on or before deadline to.")
    query = select(Obligation).outerjoin(Course).join(Source)
    if q.strip():
        query = query.where(or_(*(column.icontains(q.strip(), autoescape=True) for column in (
            Obligation.title, Obligation.description, Course.code, Course.name, Source.name))))
    for column, value in ((Obligation.course_id, course_id), (Obligation.source_id, source_id),
                          (Obligation.obligation_type, obligation_type), (Obligation.status, status)):
        if value is not None:
            query = query.where(column == value)
    if deadline_from:
        query = query.where(Obligation.deadline >= deadline_from)
    if deadline_to:
        query = query.where(Obligation.deadline <= deadline_to)
    if missing_deadline:
        query = query.where(Obligation.deadline.is_(None))
    count = db.scalar(select(func.count()).select_from(query.subquery()))
    column = {"deadline": Obligation.deadline, "title": Obligation.title, "course": Course.code,
              "type": Obligation.obligation_type, "status": Obligation.status, "recorded_at": Obligation.recorded_at}[sort_by]
    query = query.order_by(column.is_(None), column.desc() if order == "desc" else column.asc(), Obligation.id)
    records = db.scalars(query.options(joinedload(Obligation.course), joinedload(Obligation.source)).offset(offset).limit(limit))
    return {"items": [obligation_json(o) for o in records], "total": count, "offset": offset, "limit": limit}


def validate_references(db, data):
    if not db.get(Source, data.source_id):
        raise HTTPException(422, "source_id does not reference an existing source.")
    if data.course_id is not None and not db.get(Course, data.course_id):
        raise HTTPException(422, "course_id does not reference an existing course.")


@router.post("/obligations", status_code=201, tags=["Obligations"])
def create_obligation(data: ObligationWrite, db: Session = Depends(get_db)):
    validate_references(db, data)
    item = Obligation(**data.model_dump())
    db.add(item)
    touch_data(db)
    db.commit()
    return obligation_json(item)


@router.get("/obligations/{identifier}", tags=["Obligations"])
def obligation(identifier: int, db: Session = Depends(get_db)):
    return obligation_json(get_or_404(db, Obligation, identifier))


@router.put("/obligations/{identifier}", tags=["Obligations"])
def update_obligation(identifier: int, data: ObligationWrite, db: Session = Depends(get_db)):
    item = get_or_404(db, Obligation, identifier)
    validate_references(db, data)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    # Expire relationship caches when a foreign key changes.
    db.flush()
    db.expire(item, ["course", "source"])
    touch_data(db)
    db.commit()
    return obligation_json(item)


@router.delete("/obligations/{identifier}", status_code=204, tags=["Obligations"])
def delete_obligation(identifier: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Obligation, identifier)
    db.delete(item)
    touch_data(db)
    db.commit()
    return Response(status_code=204)
