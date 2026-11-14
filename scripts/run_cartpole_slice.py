"""Acceptance script — the real CartPole vertical slice (Phases 1–6).

Runs the full slice against a fresh SQLite database and local
artifact storage, using the real FastAPI app (TestClient) for API
calls and the real worker CLI (``syrius-worker run --once``) for
every job — training included. Nothing is mocked.

Config is the plan §10.2 reference exactly: CartPole-v1, seed 42,
PPO, 20000 timesteps, lr 0.0003, n_steps 2048, batch 64, n_epochs 10,
gamma 0.99, gae_lambda 0.95, clip_range 0.2, eval 20 episodes,
deterministic, seed 100.

Usage:
    uv run --project apps/api python scripts/run_cartpole_slice.py

Writes var/results/cartpole-slice-<ts>/results.json + report.md.
Exit 0 only when training, evaluation and export validation all
succeeded with measured numbers.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

RESULTS_DIR = ROOT / "var" / "results"


def find_uv() -> str:
    import shutil

    found = shutil.which("uv")
    if found:
        return found
    candidate = Path.home() / ".local" / "bin" / "uv"
    if candidate.exists():
        return str(candidate)
    raise RuntimeError("uv not found on PATH or ~/.local/bin")


def worker_run_once(env: dict, timeout: int = 1800) -> dict:
    """Run the real worker CLI once against *env* (DATABASE_URL set)."""
    proc = subprocess.run(
        [find_uv(), "run", "--project", "apps/worker", "python", "-m", "syrius_worker.main", "run", "--once"],
        cwd=ROOT,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr[-2000:]}


def wait_for_job(client, job_id: str, timeout: int = 1800) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/v1/jobs/{job_id}").json()
        if job["status"] in ("completed", "failed", "cancelled"):
            return job
        time.sleep(2)
    raise TimeoutError(f"job {job_id} did not finish in {timeout}s")


def main() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = RESULTS_DIR / f"cartpole-slice-{timestamp}"
    storage_dir = out_dir / "storage"
    db_path = out_dir / "syrius.db"
    out_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{db_path}"
    env = {"DATABASE_URL": db_url, "STORAGE_DIR": str(storage_dir)}

    os.environ["DATABASE_URL"] = db_url
    os.environ["STORAGE_DIR"] = str(storage_dir)

    from fastapi.testclient import TestClient

    from syrius_api.db import make_engine
    from syrius_api.main import app
    from syrius_api.models import Base
    from syrius_api.routers import get_db
    from syrius_api.db import make_session_factory
    from syrius_api import rl

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
    results: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "steps": {}}

    def record(step: str, payload: dict) -> None:
        results["steps"][step] = payload
        print(f"[{step}] {json.dumps(payload, default=str)[:400]}")

    started = time.time()

    project = client.post("/api/v1/projects", json={"name": "cartpole-slice"}).json()
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
    record("specification", {"id": spec["id"], "status": formal["status"], "gaps": formal["gaps"]})
    env_row = client.post(
        "/api/v1/environments",
        json={"project_id": project["id"], "name": "cartpole-v1", "gym_id": "CartPole-v1"},
    ).json()
    record("environment", {"id": env_row["id"], "gym_id": env_row["gym_id"], "status": env_row["status"]})
    experiment = client.post(
        "/api/v1/experiments",
        json={"project_id": project["id"], "environment_id": env_row["id"], "name": "ppo-cartpole-20000"},
    ).json()
    assert experiment["config"]["total_timesteps"] == 20000, "config is not the §10.2 reference"
    record("experiment", {"id": experiment["id"], "config": experiment["config"]})

    # Baseline (random policy, 20 episodes) via the real worker.
    baseline = client.post(
        f"/api/v1/experiments/{experiment['id']}/baseline", json={"episodes": 20, "seed": 0}
    ).json()
    run = worker_run_once(env)
    assert run["returncode"] == 0, f"worker failed on baseline: {run['stdout']}\n{run['stderr']}"
    baseline_job = wait_for_job(client, baseline["job_id"])
    assert baseline_job["status"] == "completed", baseline_job
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
    record("evaluation", eval_job["result"])

    # Export + independent package validation.
    export = client.post(f"/api/v1/policies/{policy['id']}/export").json()
    run = worker_run_once(env)
    assert run["returncode"] == 0, f"worker failed on export: {run['stdout']}\n{run['stderr']}"
    export_job = wait_for_job(client, export["job_id"])
    assert export_job["status"] == "completed", export_job
    record("export", export_job["result"])
    package_uri = export_job["result"]["storage_uri"]
    package_path = storage_dir / package_uri[len("local://") :]
    independent = rl.validate_delivery_package(package_path, "CartPole-v1", n_episodes=5, seed=1000)
    record("independent_package_validation", independent)
    assert independent["valid"] is True

    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    results["wall_seconds_total"] = round(time.time() - started, 1)
    results["framework_versions"] = rl.framework_versions()
    (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    baseline_r = results["steps"]["baseline"]
    eval_r = results["steps"]["evaluation"]
    train_r = results["steps"]["training"]
    report = (
        "# CartPole slice — measured results\n\n"
        f"Run: {timestamp} (SQLite local, worker CLI, no mocks)\n\n"
        "## Baseline (random policy, 20 episodes)\n\n"
        f"- mean reward: {baseline_r['mean_reward']:.2f}\n"
        f"- median reward: {baseline_r['median_reward']:.2f}\n"
        f"- mean length: {baseline_r['mean_length']:.2f}\n\n"
        "## Training (PPO, 20000 steps, seed 42)\n\n"
        f"- wall time: {train_r['wall_seconds']}s\n"
        f"- final mean episode reward: {train_r.get('final_mean_episode_reward')}\n"
        f"- best mean episode reward: {train_r.get('best_mean_episode_reward')}\n\n"
        "## Evaluation (20 episodes, deterministic, seed 100)\n\n"
        f"- mean reward: {eval_r['mean_reward']:.2f}\n"
        f"- median reward: {eval_r['median_reward']:.2f}\n"
        f"- mean length: {eval_r['mean_length']:.2f}\n"
        f"- success rate (500-step episodes): {eval_r['success_rate']:.2f} "
        f"({eval_r['successes']}/{eval_r['episodes']})\n\n"
        "## Export\n\n"
        f"- package: {package_uri}\n"
        f"- independent validation (5 episodes, seed 1000): "
        f"valid={independent['valid']}, mean reward {independent['mean_reward']:.2f}, "
        f"success rate {independent['success_rate']:.2f}\n"
    )
    (out_dir / "report.md").write_text(report)
    print(f"\nResults: {out_dir / 'results.json'}")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
