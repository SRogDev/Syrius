"""Tests: full CartPole API slice — project → spec → env → experiment
→ baseline job → small PPO train job → evaluate → policy → export.

Training here uses a small config (512 steps) so the suite stays
fast; the real 20000-step run is the acceptance script
``scripts/run_cartpole_slice.py``, not this test.
"""

from syrius_api.executor import execute_job


def _setup_slice(client):
    project = client.post("/api/v1/projects", json={"name": "slice"}).json()
    spec = client.post(
        "/api/v1/specifications",
        json={
            "project_id": project["id"],
            "title": "Balance the pole",
            "problem_text": "balance the pole upright",
        },
    ).json()
    url = f"/api/v1/specifications/{spec['id']}/formalize"
    formal = client.post(url, json={"gym_id": "CartPole-v1"}).json()
    env = client.post(
        "/api/v1/environments",
        json={"project_id": project["id"], "name": "cartpole", "gym_id": "CartPole-v1"},
    ).json()
    experiment = client.post(
        "/api/v1/experiments",
        json={"project_id": project["id"], "environment_id": env["id"], "name": "ppo-mini"},
    ).json()
    return project, formal, env, experiment


def test_full_slice(client, session_factory) -> None:
    project, formal, env, experiment = _setup_slice(client)
    assert formal["observation_space"]["shape"] == [4]
    assert formal["approach"]["approach"] == "PPO"
    assert env["status"] == "validated"

    # Baseline job runs for real via the executor.
    baseline = client.post(
        f"/api/v1/experiments/{experiment['id']}/baseline", json={"episodes": 5, "seed": 0}
    ).json()
    result = execute_job(session_factory, baseline["job_id"])
    assert result["policy"] == "random"
    assert result["episodes"] == 5
    job = client.get(f"/api/v1/jobs/{baseline['job_id']}").json()
    assert job["status"] == "completed"

    # Small PPO train (512 steps) via the executor.
    train = client.post(
        f"/api/v1/experiments/{experiment['id']}/train",
        json={
            "config": {
                "env_id": "CartPole-v1",
                "seed": 42,
                "total_timesteps": 512,
                "n_steps": 128,
                "batch_size": 64,
                "n_epochs": 2,
            }
        },
    ).json()
    train_result = execute_job(session_factory, train["job_id"])
    assert train_result["total_timesteps"] == 512
    metrics = client.get(f"/api/v1/experiments/{experiment['id']}/metrics").json()
    assert metrics["status"] == "completed"
    assert metrics["current_step"] == 512
    checkpoints = client.get(f"/api/v1/experiments/{experiment['id']}/checkpoints").json()
    assert len(checkpoints) == 1

    # Policy from the checkpoint, then evaluation + export.
    policy = client.post(
        "/api/v1/policies", json={"experiment_id": experiment["id"], "name": "ppo-mini-policy"}
    ).json()
    assert policy["artifact_id"] == checkpoints[0]["artifact_id"]
    evaluation = client.post(
        f"/api/v1/experiments/{experiment['id']}/evaluate",
        json={"policy_id": policy["id"], "episodes": 5, "seed": 100},
    ).json()
    eval_result = execute_job(session_factory, evaluation["job_id"])
    assert eval_result["episodes"] == 5
    assert 0.0 <= eval_result["success_rate"] <= 1.0
    eval_body = client.get(f"/api/v1/evaluations/{evaluation['evaluation_run_id']}").json()
    assert eval_body["status"] == "completed"
    report = client.get(f"/api/v1/evaluations/{evaluation['evaluation_run_id']}/report").json()
    assert report["report_json"]["episodes"] == 5

    export = client.post(f"/api/v1/policies/{policy['id']}/export").json()
    export_result = execute_job(session_factory, export["job_id"])
    assert export_result["validation"]["valid"] is True
    assert export_result["manifest"]["env_id"] == "CartPole-v1"
    assert export_result["manifest"]["seeds"] == {"training": 42, "evaluation": 100}
    policy_body = client.get(f"/api/v1/policies/{policy['id']}").json()
    assert policy_body["status"] == "exported"


def test_train_is_enqueued_not_inline(client) -> None:
    _project, _formal, _env, experiment = _setup_slice(client)
    train = client.post(
        f"/api/v1/experiments/{experiment['id']}/train",
        json={"config": {"total_timesteps": 512, "n_steps": 128, "batch_size": 64, "n_epochs": 1}},
    ).json()
    assert train["job_id"]
    job = client.get(f"/api/v1/jobs/{train['job_id']}").json()
    assert job["status"] == "queued"  # still queued: nothing ran in the request


def test_validate_endpoint_and_tools_listing(client) -> None:
    body = client.post("/api/v1/environments/validate", json={"gym_id": "CartPole-v1"}).json()
    assert body["valid"] is True
    assert body["observation_space"]["shape"] == [4]
    listing = client.get("/api/v1/capabilities/tools").json()
    assert len(listing) == 71
    seeded = client.post("/api/v1/capabilities/seed-tools").json()
    assert seeded["seeded"] == 71


def test_sse_progress_stream(client, session_factory) -> None:
    _project, _formal, _env, experiment = _setup_slice(client)
    train = client.post(
        f"/api/v1/experiments/{experiment['id']}/train",
        json={"config": {"total_timesteps": 256, "n_steps": 128, "batch_size": 64, "n_epochs": 1}},
    ).json()
    execute_job(session_factory, train["job_id"])
    with client.stream("GET", f"/api/v1/experiments/{experiment['id']}/events") as response:
        assert response.status_code == 200
        body = response.read().decode()
    assert "completed" in body
    assert "current_step" in body


def test_404s_and_validation(client) -> None:
    assert client.get("/api/v1/projects/nope").status_code == 404
    assert client.get("/api/v1/experiments/nope").status_code == 404
    assert client.post("/api/v1/projects", json={"name": ""}).status_code == 422
    assert client.post(
        "/api/v1/experiments", json={"project_id": "nope", "environment_id": "nope", "name": "x"}
    ).status_code == 404


def test_workflow_run_creates_experiment_and_job(client, session_factory) -> None:
    project, _formal, env, _experiment = _setup_slice(client)
    workflow = client.post(
        "/api/v1/workflows", json={"project_id": project["id"], "name": "wf-1"}
    ).json()
    run = client.post(
        f"/api/v1/workflows/{workflow['id']}/run",
        json={
            "environment_id": env["id"],
            "name": "wf-exp",
            "config": {"total_timesteps": 256, "n_steps": 128, "batch_size": 64, "n_epochs": 1},
        },
    ).json()
    assert run["experiment_id"]
    assert run["job_id"]
    assert run["thread_id"]
    result = execute_job(session_factory, run["job_id"])
    assert result["total_timesteps"] == 256
    fetched = client.get(f"/api/v1/workflows/{workflow['id']}").json()
    assert fetched["executions"][0]["status"] == "completed"
    assert fetched["executions"][0]["state"]["status"] == "training_queued"
    cancelled = client.post(f"/api/v1/workflows/{workflow['id']}/cancel").json()
    assert cancelled["status"] == "cancelled"
