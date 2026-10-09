"""FastAPI entry point: python -m uvicorn backend.main:app --reload"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from .database import init_db, make_engine, make_session_factory
from .reconciliation import RuleConfig
from .routers import dashboard, records, reviews


def create_app(database_url=None, rule_config=None):
    engine = make_engine(database_url)

    @asynccontextmanager
    async def lifespan(application):
        init_db(engine)
        yield
        engine.dispose()

    application = FastAPI(title="Student Academic Obligation Reconciliation System",
                          version="1.0.0", description="CAP205 · Local, rule-based prototype. All sources are manually recorded.",
                          lifespan=lifespan)
    application.state.engine = engine
    application.state.session_factory = make_session_factory(engine)
    application.state.rule_config = rule_config or RuleConfig.from_env()
    application.add_middleware(CORSMiddleware,
        allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(","),
        allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])

    @application.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc):
        return JSONResponse(status_code=409, content={"detail": "A duplicate value or related record prevents this change. Check course codes, source names and references."})

    @application.exception_handler(OperationalError)
    async def database_error(request: Request, exc):
        logging.getLogger(__name__).error("Database operation failed", exc_info=exc)
        return JSONResponse(status_code=503, content={"detail": "The database is busy or unavailable. Try again shortly."})

    @application.get("/health", tags=["System"])
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "sqlite", "mode": "local-manual-entry"}

    @application.get("/", include_in_schema=False)
    def home():
        return RedirectResponse("/app/index.html")

    application.include_router(records.router)
    application.include_router(reviews.router)
    application.include_router(dashboard.router)
    frontend = Path(__file__).resolve().parent.parent / "frontend"
    if frontend.exists():
        application.mount("/app", StaticFiles(directory=str(frontend), html=True), name="frontend")
    return application


app = create_app()
