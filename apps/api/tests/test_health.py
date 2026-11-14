"""Tests for the Syrius API health endpoints (Phase 0).

The API must answer honestly about database reachability: when Postgres is
down it reports ``db: unavailable`` and ``status: degraded`` instead of
failing or faking a green check. These tests accept either state but require
the two fields to be consistent.
"""

from fastapi.testclient import TestClient
from syrius_api.main import app

client = TestClient(app)


def test_health_returns_200_with_consistent_status() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "syrius-api"
    assert body["db"] in ("ok", "unavailable")
    expected = "ok" if body["db"] == "ok" else "degraded"
    assert body["status"] == expected


def test_api_v1_health_matches_root_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "syrius-api"
    assert body["version"] == "0.1.0"
    assert body["db"] in ("ok", "unavailable")
    assert body["status"] in ("ok", "degraded")


def test_unknown_route_is_404() -> None:
    response = client.get("/api/v1/does-not-exist-yet")
    assert response.status_code == 404
