"""Synthetic scenarios only. Safe repeat: an already seeded DB is unchanged."""
import argparse
from datetime import date, timedelta

from sqlalchemy import func, select

from .database import init_db, make_engine, make_session_factory, utcnow
from .models import AppState, Course, Obligation, Source


def seed_database(db):
    state = db.get(AppState, 1)
    if state.synthetic_data:
        return {"seeded": False, "message": "Synthetic sample data was already loaded; nothing changed."}
    if any(db.scalar(select(func.count()).select_from(model)) for model in (Course, Source, Obligation)):
        raise ValueError("Seed requires an empty database, so real records are never mixed with sample data. Use a separate DATABASE_URL.")
    now = utcnow()
    java = Course(code="CAP201", name="Java Programming")
    computing = Course(code="CAP205", name="Next Gen Computing")
    maths = Course(code="MTH101", name="Discrete Mathematics")
    lms = Source(name="LMS", source_type="LMS", description="SYNTHETIC · Manually transcribed demo LMS entries. No live connection.", last_checked_at=now)
    notice = Source(name="Faculty Notice", source_type="Faculty Notice", description="SYNTHETIC · Demo faculty notice, recorded manually.", last_checked_at=now)
    email = Source(name="Course Email", source_type="Email", description="SYNTHETIC · Manually entered email details. No inbox access.", last_checked_at=now)
    pdf = Source(name="Semester Handbook", source_type="PDF", description="SYNTHETIC · Demo handbook entry. No PDF parsing.", last_checked_at=now - timedelta(days=65))
    db.add_all([java, computing, maths, lms, notice, email, pdf])
    db.flush()
    rows = [
        (java, "Assignment 2", "Assignment", date(2026, 10, 20), lms, "Required scenario A: LMS states 20 October. Neither source is assumed correct."),
        (java, "Assignment 2", "Assignment", date(2026, 10, 22), notice, "Required scenario B: faculty notice states 22 October. Needs verification."),
        (computing, "Prototype project submission", "Project", date(2026, 10, 28), lms, "Genuine matching pair, source A."),
        (computing, "  PROTOTYPE project submission!  ", "Project", date(2026, 10, 28), email, "Genuine matching pair, source B. Original punctuation and spacing are preserved."),
        (java, "Collections quiz", "Quiz", date(2026, 10, 16), lms, "Potential pair: the other source has not recorded a deadline."),
        (java, "Collections Quiz", "Quiz", None, email, "Missing deadline. Do not infer it from LMS."),
        (maths, "Assignment 2", "Assignment", date(2026, 10, 20), lms, "Same title as Java but a different course: unrelated."),
        (computing, "", None, None, notice, "Incomplete notice: course known; title, type and deadline not yet recorded."),
        (maths, "Graph theory examination", "Examination", date(2026, 11, 5), notice, "Unrelated topic; candidate blocking skips unrelated pairs."),
        (computing, "Research ethics declaration", "Other", date(2026, 9, 15), pdf, "Old active record from a source not checked recently; possible outdated information."),
        (computing, "Project proposal", "Project", date(2026, 10, 12), lms, "Partial title similarity example."),
        (computing, "Project proposal draft", "Project", date(2026, 10, 12), email, "May be a distinct draft milestone. Verify identity."),
    ]
    for index, (course, title, kind, deadline, source, description) in enumerate(rows):
        record = Obligation(course_id=course.id, title=title, obligation_type=kind, deadline=deadline,
                            source_id=source.id, description="SYNTHETIC · " + description,
                            recorded_at=now - timedelta(minutes=len(rows) - index), updated_at=now)
        if index == 9:
            record.recorded_at = now - timedelta(days=65)
            record.updated_at = now - timedelta(days=65)
        db.add(record)
    state.synthetic_data = True
    state.data_revision += 1
    db.commit()
    return {"seeded": True, "message": "Loaded 12 synthetic obligations, 4 sources and 3 courses. Run reconciliation in the app."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    engine = make_engine()
    init_db(engine)
    try:
        with make_session_factory(engine)() as db:
            print(seed_database(db)["message"])
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
