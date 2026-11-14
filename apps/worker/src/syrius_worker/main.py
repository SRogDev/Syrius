"""Syrius worker: registration + heartbeat/status CLI (Phase 0) and the
job execution loop (Phase 3).

The ``run`` command claims jobs from the Postgres-backed queue
(``syrius_api.jobs``), executes them through ``syrius_api.executor``
(train / baseline / evaluate / export), heartbeats the lease, and
records completion/failure with retries. It runs as a plain local
process (``uv run``) for the slice; Docker is the deployment target.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DEFAULT_NAME = "syrius-worker-1"
DEFAULT_URL = "postgresql+psycopg://syrius:syrius@localhost:5432/syrius"


def _engine() -> Any:
    url = os.environ.get("DATABASE_URL", DEFAULT_URL)
    if url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 2})


def _short_reason(exc: Exception) -> str:
    message = str(exc).splitlines()
    return message[0].strip() if message else "connection failed"


def _is_sqlite() -> bool:
    return os.environ.get("DATABASE_URL", DEFAULT_URL).startswith("sqlite")


def _now_sql() -> str:
    return "datetime('now')" if _is_sqlite() else "now()"


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
                        "(name, status, last_heartbeat_at, created_at, updated_at) "
                        f"VALUES (:name, 'alive', {_now_sql()}, {_now_sql()}, {_now_sql()}) "
                        "ON CONFLICT (name) DO UPDATE SET "
                        f"status = 'alive', last_heartbeat_at = {_now_sql()}"
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


def _upsert_worker_row(name: str) -> None:
    """Upsert the ``workers`` row for this process (Phase 3 identity)."""
    from syrius_api.db import make_session_factory
    from syrius_api.models import Worker, utcnow

    factory = make_session_factory(os.environ.get("DATABASE_URL", DEFAULT_URL))
    session = factory()
    try:
        row = session.query(Worker).filter_by(name=name).first()
        if row is None:
            row = Worker(
                name=name,
                status="alive",
                capabilities={"jobs": ["train", "baseline", "evaluate", "export"]},
            )
            session.add(row)
        row.status = "alive"
        row.last_heartbeat_at = utcnow()
        session.commit()
    finally:
        session.close()


def run_loop(
    name: str = DEFAULT_NAME,
    once: bool = False,
    poll_seconds: float = 2.0,
    max_jobs: int = 0,
) -> int:
    """Claim and execute jobs until the queue is empty (``once``) or
    forever. Returns 0 when every executed job completed; 1 when a job
    failed terminally or the DB is unreachable."""
    from syrius_api.db import make_session_factory
    from syrius_api.executor import execute_job
    from syrius_api.jobs import claim_job

    url = os.environ.get("DATABASE_URL", DEFAULT_URL)
    factory = make_session_factory(url)
    try:
        _upsert_worker_row(name)
    except Exception as exc:  # noqa: BLE001 — report honestly, do not crash
        payload = {"worker": "syrius-worker", "db": "unavailable", "reason": _short_reason(exc)}
        print(json.dumps(payload))
        return 1
    executed = 0
    failed = 0
    while True:
        session = factory()
        try:
            job = claim_job(session, worker_name=name)
        finally:
            session.close()
        if job is None:
            if once:
                break
            time.sleep(poll_seconds)
            continue
        print(json.dumps({"worker": name, "job_id": job.id, "kind": job.kind, "status": "claimed"}))
        try:
            execute_job(factory, job.id)
            executed += 1
        except Exception as exc:  # noqa: BLE001 — execute_job already failed the job
            failed += 1
            failed_payload = {
                "worker": name,
                "job_id": job.id,
                "status": "failed",
                "error": str(exc),
            }
            print(json.dumps(failed_payload))
        if once or (max_jobs and executed + failed >= max_jobs):
            break
    print(json.dumps({"worker": name, "executed": executed, "failed": failed}))
    return 0 if failed == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="syrius-worker")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("status", "heartbeat"):
        p = sub.add_parser(cmd, help=f"{cmd} the worker registration")
        p.add_argument("--name", default=DEFAULT_NAME)
    run_parser = sub.add_parser("run", help="claim and execute jobs from the queue")
    run_parser.add_argument("--name", default=DEFAULT_NAME)
    run_parser.add_argument(
        "--once", action="store_true", help="execute one job (if any) then exit"
    )
    run_parser.add_argument(
        "--max-jobs", type=int, default=0, help="stop after N jobs (0 = unlimited)"
    )
    run_parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_loop(
            name=args.name, once=args.once, poll_seconds=args.poll_seconds, max_jobs=args.max_jobs
        )
    result = worker_status(args.name) if args.command == "status" else heartbeat(args.name)
    print(json.dumps(result, indent=2, default=str))
    return (
        0
        if result.get("db") == "ok" and (args.command == "status" or result.get("registered"))
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
