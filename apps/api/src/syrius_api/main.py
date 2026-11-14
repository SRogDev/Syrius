"""Syrius API — FastAPI application (Phases 0–6).

Phase 0: health endpoints with honest DB reachability. Phases 1–6:
the full versioned API (projects, specs, environments, experiments,
training jobs, evaluations, policies, capabilities, workflows,
workers, events) — see ``routers.py``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .db import engine
from .routers import router as v1_router
from .settings import settings

logger = logging.getLogger(__name__)

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="Syrius API", version=VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_db() -> str:
    """Return ``"ok"`` if PostgreSQL answers, else ``"unavailable"``."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except SQLAlchemyError as exc:
        logger.warning("Database unreachable: %s", exc)
        return "unavailable"


def health_payload() -> dict[str, str]:
    """Shared shape for both health endpoints."""
    db_status = check_db()
    return {
        "service": "syrius-api",
        "version": VERSION,
        "environment": settings.environment,
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness/health probe (root path, for load balancers and the web)."""
    return health_payload()


@app.get("/api/v1/health")
def health_v1() -> dict[str, str]:
    """Versioned health probe used by the web frontend."""
    return health_payload()


app.include_router(v1_router)
