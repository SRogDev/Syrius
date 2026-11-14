"""Database engine for the Syrius API (Phases 0–6).

PostgreSQL is canonical (``DATABASE_URL`` defaults to the Compose
Postgres). SQLite is supported for local development and tests: any
``sqlite`` URL gets ``check_same_thread=False`` and no Postgres-only
connect args, so the whole backend — including real CartPole training —
runs without Docker. The Postgres live path is exercised in CI.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .settings import settings


def make_engine(url: str | None = None) -> Engine:
    """Build an engine for *url* (or the configured default)."""
    db_url = url or settings.database_url
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )
    return create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 2},
    )


def make_session_factory(url: str | None = None) -> sessionmaker[Session]:
    """Session factory bound to an engine for *url*."""
    return sessionmaker(bind=make_engine(url), autoflush=False, expire_on_commit=False)


engine: Engine = make_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)


def get_session() -> Session:
    """Return a new session bound to the default engine (FastAPI dep)."""
    return SessionLocal()
