"""End-to-end acceptance test — the real CartPole vertical slice (Phase 7).

Runs the full slice against a fresh SQLite database and local
artifact storage, using the real FastAPI app (TestClient) for API
calls and the real worker CLI (``syrius-worker run --once``) for
every job — training included. Nothing is mocked, no metric is
faked: every asserted number is measured in this run.

Flow: project → spec → formalize → environment → experiment
(§10.2 config) → record one episode → random baseline → PPO
training (20000 steps) → training history → independent evaluation
(20 eps) → report → policy export → artifact download (bytes +
sha256) → independent package load + rollouts.

Success thresholds are deliberately loose bounds, not exact
stochastic rewards — the 2026-11-14 measured run met them with
wide margin (baseline mean 23.35 vs bound < 100; evaluation mean
498.70 vs bound >= 400; export validation mean 492.80 vs bound
>= 300). A run that trains a broken policy fails the evaluation
and export bounds instead of passing on structure alone.

Usage:
    uv run --project apps/api python scripts/e2e_cartpole.py

Writes var/results/e2e-cartpole-<ts>/results.json + report.md.
Exit 0 only when every step succeeded with measured numbers.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

RESULTS_DIR = ROOT / "var" / "results"

# Loose success bounds (see module docstring for provenance).
BASELINE_MEAN_MAX = 100.0
EVAL_MEAN_MIN = 400.0
EVAL_SUCCESS_MIN = 0.5
EXPORT_MEAN_MIN = 300.0
EXPORT_SUCCESS_MIN = 0.4


def main() -> int:
    from run_cartpole_slice import wait_for_job, worker_run_once

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out_dir = RESULTS_DIR / f"e2e-cartpole-{timestamp}"
    storage_dir = out_dir / "storage"
    db_path = out_dir / "syrius.db"
    out_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{db_path}"
    env = {"DATABASE_URL": db_url, "STORAGE_DIR": str(storage_dir)}

    os.environ["DATABASE_URL"] = db_url
    os.environ["STORAGE_DIR"] = str(storage_dir)

    from fastapi.testclient import TestClient
    from syrius_api import rl
    from syrius_api.db import make_engine, make_session_factory
    from syrius_api.main import app
    from syrius_api.models import Base
    from syrius_api.routers import get_db

    Base.metadata.create_all(make_engine(db_url))
    factory = make_session_factory(db_url)

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    results: dict = {"started_at": datetime.now(UTC).isoformat(), "steps": {}}

    def record(step: str, payload: dict) -> None:
        results["steps"][step] = payload
        print(f"[{step}] {json.dumps(payload, default=str)[:400]}")

    started = time.time()

    project = client.post("/api/v1/projects", json={"name": "e2e-cartpole"}).json()
    spec = client.post(
        "/api/v1/specifications",
        json={
            "project_id": project["id"],
            "title": "Balance the CartPole",
            "problem_text": "Keep the pole balanced by moving the cart left or right.",
        },
    ).json()
    formal = client.post(
        f"/api/v1/specifications/{spec['id']}/formalize", json={"gym_id": "CartPole-v1"}
    ).json()
    assert formal["status"] == "reviewed", formal
    assert formal["gaps"] == [], formal
    record("specification", {"id": spec["id"], "status": formal["status"]})
    env_row = client.post(
        "/api/v1/environments",
        json={"project_id": project["id"], "name": "cartpole-v1", "gym_id": "CartPole-v1"},
    ).json()
    assert env_row["status"] == "validated", env_row
    record("environment", {"id": env_row["id"], "gym_id": env_row["gym_id"]})
    experiment = client.post(
        "/api/v1/experiments",
        json={
            "project_id": project["id"],
            "environment_id": env_row["id"],
            "name": "ppo-cartpole-20000",
        },
    ).json()
    assert experiment["config"]["total_timesteps"] == 20000, "config is not the §10.2 reference"
    assert experiment["config"]["seed"] == 42
    record("experiment", {"id": experiment["id"]})

    # Phase 7 list endpoints: the new experiment shows up filtered by project.
    listed = client.get(f"/api/v1/experiments?project_id={project['id']}").json()
    assert [row["id"] for row in listed] == [experiment["id"]], listed
    record("list_experiments", {"count": len(listed)})

    # One recorded episode (random policy) via the real tool + trace read.
    recorded = client.post(
        "/api/v1/capabilities/tools/RecordEpisode/run",
        json={"environment_id": env_row["id"], "seed": 7},
    ).json()
    episode_id = recorded["episode_id"]
    listed_eps = client.get(f"/api/v1/episodes?environment_id={env_row['id']}").json()
    assert episode_id in [row["id"] for row in listed_eps], listed_eps
    trace = client.get(f"/api/v1/episodes/{episode_id}/trace").json()
    assert len(trace["steps"]) == recorded["length"], trace
    record("recorded_episode", {"id": episode_id, "length": recorded["length"]})

    # Baseline (random policy, 20 episodes) via the real worker.
    baseline = client.post(
        f"/api/v1/experiments/{experiment['id']}/baseline", json={"episodes": 20, "seed": 0}
    ).json()
    run = worker_run_once(env)
    assert run["returncode"] == 0, f"worker failed on baseline: {run['stdout']}\n{run['stderr']}"
    baseline_job = wait_for_job(client, baseline["job_id"])
    assert baseline_job["status"] == "completed", baseline_job
    assert baseline_job["result"]["episodes"] == 20
    assert baseline_job["result"]["mean_reward"] < BASELINE_MEAN_MAX, baseline_job["result"]
    record("baseline", baseline_job["result"])

    # Real PPO training: 20000 steps, via the real worker.
    train = client.post(f"/api/v1/experiments/{experiment['id']}/train", json={}).json()
    t0 = time.time()
    run = worker_run_once(env, timeout=1800)
    train_seconds = round(time.time() - t0, 1)
    assert run["returncode"] == 0, f"worker failed on train: {run['stdout']}\n{run['stderr']}"
    train_job = wait_for_job(client, train["job_id"])
    assert train_job["status"] == "completed", train_job
    train_job["result"]["wall_seconds"] = train_seconds
    record("training", train_job["result"])
    metrics = client.get(f"/api/v1/experiments/{experiment['id']}/metrics").json()
    assert metrics["status"] == "completed" and metrics["current_step"] == 20000

    # Training history: persisted metrics.csv rows for the latest run.
    history = client.get(f"/api/v1/experiments/{experiment['id']}/history").json()
    assert history["status"] == "completed"
    assert len(history["points"]) > 0, history
    # Progress is recorded every 512 steps, so the last point is the
    # last multiple of 512 below 20000 (19969), not 20000 itself.
    assert 19000 <= history["points"][-1]["timestep"] <= 20000, history["points"][-1]
    record(
        "training_history",
        {"points": len(history["points"]), "last": history["points"][-1]},
    )

    # Policy + independent evaluation (20 episodes, seed 100).
    policy = client.post(
        "/api/v1/policies", json={"experiment_id": experiment["id"], "name": "ppo-cartpole-policy"}
    ).json()
    evaluation = client.post(
        f"/api/v1/experiments/{experiment['id']}/evaluate",
        json={"policy_id": policy["id"], "episodes": 20, "seed": 100, "deterministic": True},
    ).json()
    run = worker_run_once(env)
    assert run["returncode"] == 0, f"worker failed on evaluate: {run['stdout']}\n{run['stderr']}"
    eval_job = wait_for_job(client, evaluation["job_id"])
    assert eval_job["status"] == "completed", eval_job
    eval_result = eval_job["result"]
    assert eval_result["mean_reward"] >= EVAL_MEAN_MIN, eval_result
    assert eval_result["success_rate"] >= EVAL_SUCCESS_MIN, eval_result
    record("evaluation", eval_result)

    listed_evals = client.get(
        f"/api/v1/evaluations?experiment_id={experiment['id']}"
    ).json()
    assert evaluation["evaluation_run_id"] in [row["id"] for row in listed_evals]
    report = client.get(
        f"/api/v1/evaluations/{evaluation['evaluation_run_id']}/report"
    ).json()
    assert report["report_json"]["mean_reward"] == eval_result["mean_reward"], report
    assert report["report_json"]["success_rate"] == eval_result["success_rate"]
    record("evaluation_report", report["report_json"])

    # Export + artifact download (bytes + sha256) + independent validation.
    export = client.post(f"/api/v1/policies/{policy['id']}/export").json()
    run = worker_run_once(env)
    assert run["returncode"] == 0, f"worker failed on export: {run['stdout']}\n{run['stderr']}"
    export_job = wait_for_job(client, export["job_id"])
    assert export_job["status"] == "completed", export_job
    record("export", export_job["result"])
    artifact_id = export_job["result"]["artifact_id"]
    artifact = client.get(f"/api/v1/artifacts/{artifact_id}").json()
    download = client.get(f"/api/v1/artifacts/{artifact_id}/download")
    assert download.status_code == 200
    assert hashlib.sha256(download.content).hexdigest() == artifact["sha256"]
    assert len(download.content) == artifact["size_bytes"]
    package_path = out_dir / "policy-package.zip"
    package_path.write_bytes(download.content)
    record(
        "artifact_download",
        {"artifact_id": artifact_id, "size_bytes": len(download.content),
         "sha256": artifact["sha256"]},
    )

    independent = rl.validate_delivery_package(package_path, "CartPole-v1", n_episodes=5, seed=1000)
    record("independent_package_validation", independent)
    assert independent["valid"] is True
    assert independent["mean_reward"] >= EXPORT_MEAN_MIN, independent
    assert independent["success_rate"] >= EXPORT_SUCCESS_MIN, independent

    results["finished_at"] = datetime.now(UTC).isoformat()
    results["wall_seconds_total"] = round(time.time() - started, 1)
    results["framework_versions"] = rl.framework_versions()
    (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    baseline_r = results["steps"]["baseline"]
    eval_r = results["steps"]["evaluation"]
    train_r = results["steps"]["training"]
    ind = results["steps"]["independent_package_validation"]
    report_md = (
        "# E2E CartPole acceptance — measured results (Phase 7)\n\n"
        f"Run: {timestamp} (SQLite local, worker CLI, no mocks)\n\n"
        "## Baseline (random policy, 20 episodes)\n\n"
        f"- mean reward: {baseline_r['mean_reward']:.2f}\n"
        f"- median reward: {baseline_r['median_reward']:.2f}\n"
        f"- mean length: {baseline_r['mean_length']:.2f}\n\n"
        "## Training (PPO, 20000 steps, seed 42)\n\n"
        f"- wall time: {train_r['wall_seconds']}s\n"
        f"- final mean episode reward: {train_r.get('final_mean_episode_reward')}\n"
        f"- best mean episode reward: {train_r.get('best_mean_episode_reward')}\n"
        f"- training-history points: {results['steps']['training_history']['points']} "
        f"(last timestep {results['steps']['training_history']['last']['timestep']})\n\n"
        "## Evaluation (20 episodes, deterministic, seed 100)\n\n"
        f"- mean reward: {eval_r['mean_reward']:.2f}\n"
        f"- median reward: {eval_r['median_reward']:.2f}\n"
        f"- mean length: {eval_r['mean_length']:.2f}\n"
        f"- success rate (500-step episodes): {eval_r['success_rate']:.2f} "
        f"({eval_r['successes']}/{eval_r['episodes']})\n\n"
        "## Export\n\n"
        f"- package artifact: {artifact_id} "
        f"({results['steps']['artifact_download']['size_bytes']} bytes, "
        "downloaded via GET /artifacts/{id}/download, sha256 verified)\n"
        "- independent validation (5 episodes, seed 1000): "
        f"valid={ind['valid']}, mean reward {ind['mean_reward']:.2f}, "
        f"success rate {ind['success_rate']:.2f}\n\n"
        f"Total wall time: {results['wall_seconds_total']}s\n"
    )
    (out_dir / "report.md").write_text(report_md)
    print(f"\nResults: {out_dir / 'results.json'}")
    print(report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
