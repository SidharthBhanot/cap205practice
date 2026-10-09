from fastapi import HTTPException, Request
from sqlalchemy import update

from .database import get_db as sessions
from .models import AppState


def get_db(request: Request):
    yield from sessions(request)


def get_or_404(db, model, identifier):
    instance = db.get(model, identifier)
    if instance is None:
        raise HTTPException(404, f"{model.__name__} {identifier} was not found.")
    return instance


def touch_data(db):
    db.execute(update(AppState).where(AppState.id == 1).values(data_revision=AppState.data_revision + 1))
