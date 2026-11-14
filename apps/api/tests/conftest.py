"""Shared fixtures for the Syrius API tests (Phases 1–6).

Every test runs against a fresh SQLite file database (no Postgres in
the sandbox) with the full schema created from the ORM metadata, and
a temp storage dir. The FastAPI ``get_db`` dependency is overridden
to the test sessions.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from syrius_api import routers
from syrius_api.db import make_session_factory
from syrius_api.main import app
from syrius_api.models import Base
from syrius_api.settings import settings


@pytest.fixture()
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture()
def db_url(db_path):
    return f"sqlite:///{db_path}"


@pytest.fixture()
def session_factory(db_url):
    from syrius_api.db import make_engine

    Base.metadata.create_all(make_engine(db_url))
    return make_session_factory(db_url)


@pytest.fixture()
def session(session_factory) -> Session:
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def storage_dir(tmp_path, monkeypatch):
    path = tmp_path / "storage"
    path.mkdir()
    monkeypatch.setattr(settings, "storage_dir", str(path))
    return path


@pytest.fixture()
def client(session_factory, storage_dir):
    def _override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[routers.get_db] = _override_db
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(routers, "SessionLocal", session_factory)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    monkeypatch.undo()
