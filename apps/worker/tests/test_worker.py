"""Tests for the Syrius worker status/heartbeat CLI (Phase 0).

With no database running, the worker must report ``db: unavailable``
honestly and exit non-zero on heartbeat — never pretend it registered.
"""

from syrius_worker.main import heartbeat, worker_status


def test_status_reports_db_unavailable_without_postgres() -> None:
    status = worker_status()
    assert status["worker"] == "syrius-worker"
    assert status["db"] == "unavailable"
    assert "reason" in status


def test_heartbeat_reports_unavailable_without_postgres() -> None:
    result = heartbeat()
    assert result["db"] == "unavailable"
    assert result["registered"] is False
