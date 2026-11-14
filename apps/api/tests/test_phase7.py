"""Tests: Phase 7 gap endpoints + storage-path guard.

New in Phase 7 (small, tested additions only):
- list endpoints: GET /experiments, /evaluations, /episodes
  (optional parent-id filters)
- training history: GET /experiments/{id}/history, read from the
  persisted metrics.csv artifact of the latest training run
- artifact download: GET /artifacts/{id}/download (bytes, sha256 match)
- resolve_local_path refuses URIs that escape the storage root
"""

from __future__ import annotations

import csv
import io

import pytest
from syrius_api.executor import resolve_local_path
from syrius_api.models import Artifact, Environment, Episode, EvaluationRun, Experiment, Project
from syrius_api.settings import settings
from syrius_api.storage import LocalStorage, sha256_bytes


def _seed_project_env_experiment(client, session):
    project = Project(name="p7", description="phase7")
    session.add(project)
    session.commit()
    env = Environment(project_id=project.id, name="cartpole", gym_id="CartPole-v1")
    session.add(env)
    session.commit()
    exp = Experiment(
        project_id=project.id, environment_id=env.id, name="ppo-1", config={"seed": 42}
    )
    session.add(exp)
    session.commit()
    return project, env, exp


def test_list_experiments_filters_by_project(client, session) -> None:
    project, env, exp = _seed_project_env_experiment(client, session)
    other = Project(name="other")
    session.add(other)
    session.commit()
    other_env = Environment(project_id=other.id, name="cartpole", gym_id="CartPole-v1")
    session.add(other_env)
    session.commit()
    other_exp = Experiment(
        project_id=other.id, environment_id=other_env.id, name="ppo-2", config={}
    )
    session.add(other_exp)
    session.commit()

    resp = client.get("/api/v1/experiments")
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json()]
    assert exp.id in ids and other_exp.id in ids

    resp = client.get(f"/api/v1/experiments?project_id={project.id}")
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json()]
    assert ids == [exp.id]


def test_list_evaluations_filters_by_experiment(client, session) -> None:
    _, _, exp = _seed_project_env_experiment(client, session)
    run = EvaluationRun(experiment_id=exp.id, status="completed", metrics={"mean_reward": 10.0})
    session.add(run)
    session.commit()

    resp = client.get("/api/v1/evaluations")
    assert resp.status_code == 200
    assert [row["id"] for row in resp.json()] == [run.id]

    resp = client.get("/api/v1/evaluations?experiment_id=nonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_episodes_filters_by_environment(client, session) -> None:
    _, env, _ = _seed_project_env_experiment(client, session)
    ep = Episode(environment_id=env.id, length=23, total_reward=23.0, seed=7)
    session.add(ep)
    session.commit()

    resp = client.get("/api/v1/episodes")
    assert resp.status_code == 200
    assert [row["id"] for row in resp.json()] == [ep.id]

    resp = client.get(f"/api/v1/episodes?environment_id={env.id}")
    assert resp.status_code == 200
    assert [row["id"] for row in resp.json()] == [ep.id]


def test_training_history_reads_persisted_metrics_csv(client, session, storage_dir) -> None:
    from syrius_api.models import TrainingRun

    _, _, exp = _seed_project_env_experiment(client, session)
    run = TrainingRun(
        experiment_id=exp.id, status="completed", total_timesteps=20000, current_step=20000
    )
    session.add(run)
    session.commit()

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["timestep", "mean_episode_reward"])
    writer.writeheader()
    writer.writerow({"timestep": 512, "mean_episode_reward": 21.5})
    writer.writerow({"timestep": 1024, "mean_episode_reward": ""})
    writer.writerow({"timestep": 20000, "mean_episode_reward": 134.44})
    LocalStorage().put(
        f"training/{exp.id}/{run.id}/metrics.csv", buf.getvalue().encode()
    )

    resp = client.get(f"/api/v1/experiments/{exp.id}/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["experiment_id"] == exp.id
    assert body["training_run_id"] == run.id
    assert body["status"] == "completed"
    assert body["points"] == [
        {"timestep": 512, "mean_episode_reward": 21.5},
        {"timestep": 1024, "mean_episode_reward": None},
        {"timestep": 20000, "mean_episode_reward": 134.44},
    ]


def test_training_history_without_run_is_empty(client, session) -> None:
    _, _, exp = _seed_project_env_experiment(client, session)
    resp = client.get(f"/api/v1/experiments/{exp.id}/history")
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_run"
    assert resp.json()["points"] == []


def test_training_history_unknown_experiment_404s(client) -> None:
    resp = client.get("/api/v1/experiments/nonexistent/history")
    assert resp.status_code == 404


def test_artifact_download_returns_bytes_matching_sha256(client, session, storage_dir) -> None:
    data = b"fake-zip-bytes-policy-package"
    uri = LocalStorage().put("packages/policy-1/policy-package.zip", data)
    artifact = Artifact(
        kind="package",
        name="policy-package.zip",
        storage_uri=uri,
        size_bytes=len(data),
        sha256=sha256_bytes(data),
    )
    session.add(artifact)
    session.commit()

    resp = client.get(f"/api/v1/artifacts/{artifact.id}/download")
    assert resp.status_code == 200
    assert resp.content == data
    assert resp.headers["content-type"] == "application/octet-stream"
    assert "policy-package.zip" in resp.headers["content-disposition"]


def test_artifact_download_404_and_non_local_501(client, session) -> None:
    resp = client.get("/api/v1/artifacts/nonexistent/download")
    assert resp.status_code == 404

    artifact = Artifact(
        kind="package", name="x.zip", storage_uri="s3://bucket/x.zip",
        size_bytes=1, sha256="abc",
    )
    session.add(artifact)
    session.commit()
    resp = client.get(f"/api/v1/artifacts/{artifact.id}/download")
    assert resp.status_code == 501

    escaping = Artifact(
        kind="package", name="y.zip", storage_uri="local://../escape.zip",
        size_bytes=1, sha256="abc",
    )
    session.add(escaping)
    session.commit()
    resp = client.get(f"/api/v1/artifacts/{escaping.id}/download")
    assert resp.status_code == 400
    assert "escapes storage root" in resp.json()["detail"]


def test_resolve_local_path_refuses_escape(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))
    with pytest.raises(ValueError, match="escapes storage root"):
        resolve_local_path("local://../escape.txt")
    with pytest.raises(ValueError, match="escapes storage root"):
        resolve_local_path("local://a/../../escape.txt")
    with pytest.raises(ValueError, match="not a local storage URI"):
        resolve_local_path("s3://bucket/x.zip")
    ok = resolve_local_path("local://packages/p/policy-package.zip")
    assert str(ok).startswith(str((tmp_path / "storage").resolve()))
