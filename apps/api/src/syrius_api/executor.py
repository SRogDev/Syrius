"""Job executor (Phase 3) — what the worker runs for each job kind.

The API never runs long training inside a request handler; it enqueues
a job and the worker executes it here. Every handler is synchronous
and honest: on exception the job fails with the real error attached
(and retries per policy in ``jobs.fail_job``).

Local artifact paths: artifacts are stored under ``settings.storage_dir``
with ``storage_uri`` ``local://<key>``; ``resolve_local_path`` maps a
URI back to a filesystem path for the local backend only.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from . import jobs as queue
from . import rl
from .jobs import append_job_log, complete_job, fail_job
from .models import (
    Artifact,
    Checkpoint,
    EvaluationRun,
    Experiment,
    Job,
    Policy,
    TrainingRun,
    record_audit,
    utcnow,
)
from .schemas import TrainingConfig
from .settings import settings
from .storage import LocalStorage, sha256_bytes


def resolve_local_path(storage_uri: str) -> Path:
    """Map a ``local://`` storage URI to its filesystem path."""
    if not storage_uri.startswith("local://"):
        raise ValueError(f"not a local storage URI: {storage_uri!r}")
    return Path(settings.storage_dir).expanduser().resolve() / storage_uri[len("local://") :]


def _register_artifact(
    session: Session,
    *,
    project_id: str | None,
    kind: str,
    name: str,
    key: str,
    data: bytes,
    metadata: dict | None = None,
) -> Artifact:
    storage = LocalStorage()
    uri = storage.put(key, data)
    artifact = Artifact(
        project_id=project_id,
        kind=kind,
        name=name,
        storage_uri=uri,
        size_bytes=len(data),
        sha256=sha256_bytes(data),
        artifact_metadata=metadata or {},
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def _copy_to_storage(
    session: Session,
    *,
    project_id: str | None,
    kind: str,
    name: str,
    key: str,
    source_path: str | Path,
    metadata: dict | None = None,
) -> Artifact:
    data = Path(source_path).read_bytes()
    return _register_artifact(
        session,
        project_id=project_id,
        kind=kind,
        name=name,
        key=key,
        data=data,
        metadata=metadata,
    )


def _progress_updater(session_factory, training_run_id: str, job_id: str):
    """Callback for the training loop: persist progress + heartbeat."""

    def _on_progress(step: int, mean_reward: float | None) -> None:
        session = session_factory()
        try:
            run = session.get(TrainingRun, training_run_id)
            if run is not None:
                run.current_step = step
                metrics = dict(run.metrics or {})
                metrics["last_mean_episode_reward"] = mean_reward
                metrics["last_step"] = step
                run.metrics = metrics
                session.commit()
            job = session.get(Job, job_id)
            owner = job.lease_owner if job is not None else None
            if owner:
                queue.heartbeat_job(session, job_id=job_id, worker_name=owner)
        finally:
            session.close()

    return _on_progress


def execute_train(session_factory, session: Session, job) -> dict:
    """Job kind ``train``: PPO training for one experiment."""
    payload = job.payload
    experiment = session.get(Experiment, payload["experiment_id"])
    if experiment is None:
        raise ValueError(f"experiment not found: {payload['experiment_id']}")
    config = TrainingConfig(**payload.get("config", experiment.config or {}))
    training_run_id = payload.get("training_run_id")
    run = session.get(TrainingRun, training_run_id) if training_run_id else None
    if run is None:
        run = TrainingRun(
            experiment_id=experiment.id,
            job_id=job.id,
            status="running",
            total_timesteps=config.total_timesteps,
            started_at=utcnow(),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
    else:
        run.status = "running"
        run.job_id = job.id
        run.started_at = utcnow()
        session.commit()
    append_job_log(
        session,
        job_id=job.id,
        message=f"training started: {config.env_id} PPO {config.total_timesteps} steps",
    )
    workdir = Path(settings.storage_dir) / "training" / experiment.id / run.id
    result = rl.train_ppo(
        config,
        workdir,
        on_progress=_progress_updater(session_factory, run.id, job.id),
    )
    if queue.job_is_cancelled(session, job_id=job.id):
        raise InterruptedError("training cancelled by user")
    checkpoint = _copy_to_storage(
        session,
        project_id=experiment.project_id,
        kind="checkpoint",
        name=f"{experiment.name}-step-{config.total_timesteps}",
        key=f"checkpoints/{experiment.id}/{run.id}/final_model.zip",
        source_path=result["model_path"],
        metadata={"step": config.total_timesteps, "algorithm": "PPO"},
    )
    session.add(
        Checkpoint(
            experiment_id=experiment.id,
            training_run_id=run.id,
            step=config.total_timesteps,
            artifact_id=checkpoint.id,
        )
    )
    metrics_csv = _copy_to_storage(
        session,
        project_id=experiment.project_id,
        kind="metrics",
        name=f"{experiment.name}-metrics.csv",
        key=f"training/{experiment.id}/{run.id}/metrics.csv",
        source_path=result["metrics_path"],
    )
    run.status = "completed"
    run.current_step = config.total_timesteps
    run.metrics = result
    run.finished_at = utcnow()
    experiment.status = "trained"
    session.commit()
    record_audit(
        session,
        action="training.completed",
        entity_type="experiment",
        entity_id=experiment.id,
        details={"training_run_id": run.id, "total_timesteps": config.total_timesteps},
    )
    session.commit()
    return {
        "training_run_id": run.id,
        "checkpoint_artifact_id": checkpoint.id,
        "metrics_artifact_id": metrics_csv.id,
        "total_timesteps": config.total_timesteps,
        "final_mean_episode_reward": result.get("final_mean_episode_reward"),
        "best_mean_episode_reward": result.get("best_mean_episode_reward"),
    }


def execute_baseline(session_factory, session: Session, job) -> dict:
    """Job kind ``baseline``: random-policy baseline for an experiment."""
    payload = job.payload
    experiment = session.get(Experiment, payload["experiment_id"])
    if experiment is None:
        raise ValueError(f"experiment not found: {payload['experiment_id']}")
    config = TrainingConfig(**(payload.get("config") or experiment.config or {}))
    result = rl.run_random_baseline(
        config.env_id,
        n_episodes=payload.get("episodes", config.eval_episodes),
        seed=payload.get("seed", 0),
    )
    record_audit(
        session,
        action="baseline.completed",
        entity_type="experiment",
        entity_id=experiment.id,
        details={"mean_reward": result["mean_reward"], "episodes": result["episodes"]},
    )
    session.commit()
    return result


def execute_evaluate(session_factory, session: Session, job) -> dict:
    """Job kind ``evaluate``: independent evaluation of a policy artifact."""
    payload = job.payload
    experiment = session.get(Experiment, payload["experiment_id"])
    if experiment is None:
        raise ValueError(f"experiment not found: {payload['experiment_id']}")
    eval_run = session.get(EvaluationRun, payload["evaluation_run_id"])
    if eval_run is None:
        raise ValueError(f"evaluation run not found: {payload['evaluation_run_id']}")
    policy = session.get(Policy, payload["policy_id"]) if payload.get("policy_id") else None
    model_path: Path | None = None
    if policy is not None and policy.artifact_id:
        artifact = session.get(Artifact, policy.artifact_id)
        if artifact is not None:
            model_path = resolve_local_path(artifact.storage_uri)
    if model_path is None:
        checkpoint = (
            session.query(Checkpoint)
            .filter(Checkpoint.experiment_id == experiment.id)
            .order_by(Checkpoint.step.desc())
            .first()
        )
        if checkpoint is None:
            raise ValueError("no checkpoint available to evaluate")
        artifact = session.get(Artifact, checkpoint.artifact_id)
        model_path = resolve_local_path(artifact.storage_uri)
    config = TrainingConfig(**(payload.get("config") or experiment.config or {}))
    eval_run.status = "running"
    eval_run.started_at = utcnow()
    session.commit()
    result = rl.evaluate_policy(
        model_path,
        config.env_id,
        n_episodes=payload.get("episodes", config.eval_episodes),
        seed=payload.get("seed", config.eval_seed),
        deterministic=payload.get("deterministic", config.eval_deterministic),
    )
    eval_run.status = "completed"
    eval_run.metrics = result
    eval_run.finished_at = utcnow()
    session.commit()
    record_audit(
        session,
        action="evaluation.completed",
        entity_type="evaluation_run",
        entity_id=eval_run.id,
        details={"mean_reward": result["mean_reward"], "success_rate": result["success_rate"]},
    )
    session.commit()
    return result


def execute_export(session_factory, session: Session, job) -> dict:
    """Job kind ``export``: package a policy (model + manifest + README)
    and validate the package by independent load + rollouts."""
    payload = job.payload
    policy = session.get(Policy, payload["policy_id"])
    if policy is None:
        raise ValueError(f"policy not found: {payload['policy_id']}")
    experiment = session.get(Experiment, policy.experiment_id)
    if experiment is None:
        raise ValueError(f"experiment not found: {policy.experiment_id}")
    if not policy.artifact_id:
        raise ValueError("policy has no model artifact to export")
    artifact = session.get(Artifact, policy.artifact_id)
    model_path = resolve_local_path(artifact.storage_uri)
    config = TrainingConfig(**(experiment.config or {}))
    training_metrics = {}
    manifest = rl.build_manifest(
        env_id=config.env_id,
        env_version=1,
        scenario=None,
        algorithm=config.algorithm,
        config=config,
        training_metrics=training_metrics,
        evaluation=payload.get("evaluation") or {},
        artifact_refs={"model": artifact.storage_uri},
    )
    workdir = Path(settings.storage_dir) / "packages" / policy.id
    workdir.mkdir(parents=True, exist_ok=True)
    package_path = workdir / "policy-package.zip"
    rl.build_delivery_package(
        model_path=model_path, manifest=manifest, output_path=package_path
    )
    validation = rl.validate_delivery_package(package_path, config.env_id)
    package_artifact = _copy_to_storage(
        session,
        project_id=experiment.project_id,
        kind="package",
        name=f"{policy.name}-package.zip",
        key=f"packages/{policy.id}/policy-package.zip",
        source_path=package_path,
        metadata={"manifest": manifest, "validation": validation},
    )
    policy.status = "exported" if validation.get("valid") else "export_failed"
    policy.manifest = manifest
    session.commit()
    record_audit(
        session,
        action="policy.exported",
        entity_type="policy",
        entity_id=policy.id,
        details={"artifact_id": package_artifact.id, "valid": validation.get("valid")},
    )
    session.commit()
    return {
        "policy_id": policy.id,
        "artifact_id": package_artifact.id,
        "storage_uri": package_artifact.storage_uri,
        "manifest": manifest,
        "validation": validation,
    }


HANDLERS = {
    "train": execute_train,
    "baseline": execute_baseline,
    "evaluate": execute_evaluate,
    "export": execute_export,
}


def execute_job(session_factory, job_id: str) -> dict:
    """Execute one job to completion/failure. Returns the job result
    (or raises the recorded error after failing the job)."""
    session = session_factory()
    try:
        job = session.get(Job, job_id)
        if job is None:
            raise ValueError(f"job not found: {job_id}")
        handler = HANDLERS.get(job.kind)
        if handler is None:
            raise ValueError(f"unknown job kind: {job.kind}")
        try:
            result = handler(session_factory, session, job)
        except Exception as exc:
            fail_job(session, job_id=job.id, error=f"{type(exc).__name__}: {exc}")
            raise
        complete_job(session, job_id=job.id, result=result)
        return result
    finally:
        session.close()
