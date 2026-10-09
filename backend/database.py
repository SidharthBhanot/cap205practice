"""SQLite connection, FK enforcement and explicit schema initialization."""
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "academic.db"


def utcnow():
    """Naive UTC for consistent SQLite comparisons; API timestamps use UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


def make_engine(url=None):
    url = url or os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")
    if not url.startswith("sqlite:"):
        raise ValueError("This prototype requires a SQLite DATABASE_URL.")
    if url == f"sqlite:///{DEFAULT_DB.as_posix()}":
        DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"connect_args": {"check_same_thread": False, "timeout": 15}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine):
    from .models import AppState

    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as db:
        if db.get(AppState, 1) is None:
            db.add(AppState(id=1))
            db.commit()


def get_db(request):
    # FastAPI dependency wrapper with Request annotation lives in dependencies.py.
    with request.app.state.session_factory() as db:
        yield db


if __name__ == "__main__":
    # Import the canonical module so SQLAlchemy uses the models' Base even when
    # this file is launched as __main__.
    from backend.database import init_db as initialize, make_engine as engine_factory
    engine = engine_factory()
    initialize(engine)
    print(f"Database initialized: {engine.url}")
