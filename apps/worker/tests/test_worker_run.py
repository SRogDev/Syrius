"""Worker tests: the run loop claims and executes jobs (Phase 3)."""


import pytest
from syrius_api.db import make_engine, make_session_factory
from syrius_api.jobs import enqueue
from syrius_api.models import Base, Experiment, Project
from syrius_api.settings import settings
from syrius_worker.main import heartbeat, run_loop, worker_status


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    db_file = tmp_path / "worker.db"
    url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))
    Base.metadata.create_all(make_engine(url))
    factory = make_session_factory(url)
    session = factory()
    project = Project(name="p")
    session.add(project)
    session.commit()
    exp = Experiment(
        project_id=project.id, environment_id="env-x", name="e", config={"env_id": "CartPole-v1"}
    )
    # Environment row is not required by the baseline executor (it reads
    # the experiment config), so a placeholder id is enough here.
    session.add(exp)
    session.commit()
    yield factory, exp.id
    session.close()


def test_run_loop_executes_baseline_job(sqlite_db) -> None:
    factory, experiment_id = sqlite_db
    session = factory()
    job = enqueue(
        session,
        kind="baseline",
        payload={
            "experiment_id": experiment_id,
            "config": {"env_id": "CartPole-v1"},
            "episodes": 5,
            "seed": 0,
        },
    )
    session.close()
    assert run_loop(name="test-worker", once=True) == 0
    session = factory()
    from syrius_api.models import Job

    done = session.get(Job, job.id)
    assert done.status == "completed"
    assert done.result["policy"] == "random"
    assert done.result["episodes"] == 5
    session.close()


def test_heartbeat_and_status_on_sqlite(sqlite_db) -> None:
    assert worker_status()["db"] == "ok"
    result = heartbeat()
    assert result["db"] == "ok"
    assert result["registered"] is True
