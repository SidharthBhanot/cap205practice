"""Explicit JSON records, including immutable source snapshots for traceability."""


def timestamp(value):
    return value.isoformat(timespec="seconds") + "Z" if value else None


def course_json(course):
    return {"id": course.id, "code": course.code, "name": course.name, "created_at": timestamp(course.created_at)}


def source_json(source):
    return {"id": source.id, "name": source.name, "source_type": source.source_type,
            "description": source.description, "reference_url": source.reference_url,
            "recorded_at": timestamp(source.recorded_at), "updated_at": timestamp(source.updated_at),
            "last_checked_at": timestamp(source.last_checked_at)}


def obligation_json(record):
    return {"id": record.id, "course_id": record.course_id, "source_id": record.source_id,
            "title": record.title, "description": record.description,
            "obligation_type": record.obligation_type, "deadline": record.deadline.isoformat() if record.deadline else None,
            "status": record.status, "reference_url": record.reference_url,
            "recorded_at": timestamp(record.recorded_at), "updated_at": timestamp(record.updated_at),
            "course": course_json(record.course) if record.course else None, "source": source_json(record.source)}


def conflict_json(issue):
    return {"id": issue.id, "conflict_type": issue.conflict_type, "explanation": issue.explanation,
            "related_obligation_ids": issue.record_ids, "source_records": issue.source_records,
            "detected_at": timestamp(issue.detected_at), "last_detected_at": timestamp(issue.last_detected_at),
            "status": issue.status, "resolution_notes": issue.resolution_notes,
            "reviewed_at": timestamp(issue.reviewed_at), "is_current": issue.is_current,
            "evidence_changed": issue.evidence_changed,
            "live_obligation_ids": [record.id for record in issue.obligations]}
