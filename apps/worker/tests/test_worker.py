"""Tests for the Syrius worker status/heartbeat CLI (Phase 0).

With no database running, the worker must report ``db: unavailable``
honestly and exit non-zero on heartbeat — never pretend it registered.
The tests force an unreachable DATABASE_URL (closed port) so they
test the unavailable path deterministically even where a database
does exist — e.g. CI, where a Postgres service is running.
"""

import pytest
from syrius_worker.main import heartbeat, worker_status


@pytest.fixture(autouse=True)
def _unreachable_db(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://syrius:syrius@127.0.0.1:1/syrius"
    )


def test_status_reports_db_unavailable_without_postgres() -> None:
    status = worker_status()
    assert status["worker"] == "syrius-worker"
    assert status["db"] == "unavailable"
    assert "reason" in status


def test_heartbeat_reports_unavailable_without_postgres() -> None:
    result = heartbeat()
    assert result["db"] == "unavailable"
    assert result["registered"] is False
