"""Syrius worker (Phase 0): registration + heartbeat/status CLI.

The worker registers itself in the ``worker_registrations`` table (created
by Alembic migration 0001) so the API and operators can see it is alive.
With no database — or with migrations not applied — it says so honestly
instead of pretending to be registered.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DEFAULT_NAME = "syrius-worker-1"
DEFAULT_URL = "postgresql+psycopg://syrius:syrius@localhost:5432/syrius"


def _engine() -> Any:
    url = os.environ.get("DATABASE_URL", DEFAULT_URL)
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 2})


def _short_reason(exc: Exception) -> str:
    message = str(exc).splitlines()
    return message[0].strip() if message else "connection failed"


def worker_status(name: str = DEFAULT_NAME) -> dict[str, Any]:
    """Check DB reachability and whether this worker is registered."""
    try:
        engine = _engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            try:
                row = conn.execute(
                    text(
                        "SELECT status, last_heartbeat_at "
                        "FROM worker_registrations WHERE name = :name"
                    ),
                    {"name": name},
                ).first()
            except SQLAlchemyError as exc:
                if "does not exist" in str(exc):
                    return {
                        "worker": "syrius-worker",
                        "name": name,
                        "db": "ok",
                        "registered": False,
                        "reason": ("worker_registrations table missing — run `make migrate`"),
                    }
                raise
    except SQLAlchemyError as exc:
        return {
            "worker": "syrius-worker",
            "name": name,
            "db": "unavailable",
            "registered": False,
            "reason": _short_reason(exc),
        }
    if row is None:
        return {
            "worker": "syrius-worker",
            "name": name,
            "db": "ok",
            "registered": False,
            "reason": "no heartbeat recorded yet",
        }
    return {
        "worker": "syrius-worker",
        "name": name,
        "db": "ok",
        "registered": True,
        "status": row[0],
        "last_heartbeat_at": row[1].isoformat() if row[1] else None,
    }


def heartbeat(name: str = DEFAULT_NAME) -> dict[str, Any]:
    """Insert/update this worker's registration row. Returns its outcome."""
    try:
        engine = _engine()
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            try:
                conn.execute(
                    text(
                        "INSERT INTO worker_registrations "
                        "(name, status, last_heartbeat_at) "
                        "VALUES (:name, 'alive', now()) "
                        "ON CONFLICT (name) DO UPDATE SET "
                        "status = 'alive', last_heartbeat_at = now()"
                    ),
                    {"name": name},
                )
            except SQLAlchemyError as exc:
                if "does not exist" in str(exc):
                    return {
                        "worker": "syrius-worker",
                        "name": name,
                        "db": "ok",
                        "registered": False,
                        "reason": ("worker_registrations table missing — run `make migrate`"),
                    }
                raise
    except SQLAlchemyError as exc:
        return {
            "worker": "syrius-worker",
            "name": name,
            "db": "unavailable",
            "registered": False,
            "reason": _short_reason(exc),
        }
    return {
        "worker": "syrius-worker",
        "name": name,
        "db": "ok",
        "registered": True,
        "status": "alive",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="syrius-worker")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("status", "heartbeat"):
        p = sub.add_parser(cmd, help=f"{cmd} the worker registration")
        p.add_argument("--name", default=DEFAULT_NAME)
    args = parser.parse_args(argv)
    result = worker_status(args.name) if args.command == "status" else heartbeat(args.name)
    print(json.dumps(result, indent=2, default=str))
    return (
        0
        if result.get("db") == "ok" and (args.command == "status" or result.get("registered"))
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
