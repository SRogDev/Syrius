"""Database engine for the Syrius API (Phase 0).

A single SQLAlchemy engine. Connection attempts fail fast (2 s timeout) so
``/health`` can report ``db: unavailable`` honestly instead of hanging.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .settings import settings

engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 2},
)
