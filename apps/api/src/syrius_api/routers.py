"""API routes — Syrius Phases 1, 2, 3, 4, 6 (plan §11).

Versioned ``/api/v1/`` groups: projects, specifications, environments,
scenarios, episodes, experiments, training, checkpoints, evaluations,
policies, artifacts, capabilities, workflows, providers, workers,
events. Long work (training, evaluation, export) is always enqueued
as a job — never run inside a request handler. Live progress is SSE.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
from collections.abc import Iterator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from . import jobs as queue
from . import rl
from . import tools as tool_registry
from .db import SessionLocal
from .executor import resolve_local_path
from .models import (
    Artifact,
    AuditEvent,
    Checkpoint,
    Environment,
    Episode,
    EvaluationRun,
    EvaluationSuite,
    Experiment,
    Job,
    Policy,
    Project,
    RLProblemSpecification,
    TrainingRun,
    Worker,
    Workflow,
    WorkflowExecution,
    record_audit,
    utcnow,
)
from .schemas import (
    EnvironmentCreate,
    EnvironmentValidationOut,
    EvaluateRequest,
    ExperimentCreate,
    MetricsOut,
    ProjectCreate,
    SpecificationCreate,
    TrainingConfig,
    TrainRequest,
)
from .storage import LocalStorage

router = APIRouter(prefix="/api/v1")


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found")


def _project_out(row: Project) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "status": row.status,
        "workspace_id": row.workspace_id,
    }


def _spec_out(row: RLProblemSpecification) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "title": row.title,
        "problem_text": row.problem_text,
        "observation_space": row.observation_space or {},
        "action_space": row.action_space or {},
        "episode_structure": row.episode_structure or {},
        "constraints": row.constraints or {},
        "reward_spec": row.reward_spec or {},
        "approach": row.approach or {},
        "status": row.status,
        "gaps": row.gaps or [],
        "version": row.version,
    }


def _env_out(row: Environment) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "name": row.name,
        "gym_id": row.gym_id,
        "version": row.version,
        "config": row.config or {},
        "status": row.status,
    }


def _experiment_out(row: Experiment) -> dict:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "environment_id": row.environment_id,
        "name": row.name,
        "algorithm": row.algorithm,
        "config": row.config or {},
        "status": row.status,
    }


def _evaluation_out(row: EvaluationRun) -> dict:
    return {
        "id": row.id,
        "experiment_id": row.experiment_id,
        "policy_id": row.policy_id,
        "status": row.status,
        "metrics": row.metrics or {},
    }


def _episode_out(row: Episode) -> dict:
    return {
        "id": row.id,
        "environment_id": row.environment_id,
        "length": row.length,
        "total_reward": row.total_reward,
        "success": row.success,
        "seed": row.seed,
        "trace_artifact_id": row.trace_artifact_id,
    }


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.post("/projects", status_code=201)
def create_project(payload: ProjectCreate, session: Session = Depends(get_db)) -> dict:
    row = Project(
        name=payload.name, description=payload.description, workspace_id=payload.workspace_id
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    record_audit(session, action="project.created", entity_type="project", entity_id=row.id)
    session.commit()
    return _project_out(row)


@router.get("/projects")
def list_projects(session: Session = Depends(get_db)) -> list[dict]:
    return [_project_out(row) for row in session.query(Project).order_by(Project.created_at).all()]


@router.get("/projects/{project_id}")
def get_project(project_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Project, project_id)
    if row is None:
        raise _not_found("project")
    return _project_out(row)


# ---------------------------------------------------------------------------
# Specifications (RL Architect)
# ---------------------------------------------------------------------------


@router.post("/specifications", status_code=201)
def create_specification(payload: SpecificationCreate, session: Session = Depends(get_db)) -> dict:
    project = session.get(Project, payload.project_id)
    if project is None:
        raise _not_found("project")
    row = RLProblemSpecification(
        project_id=payload.project_id, title=payload.title, problem_text=payload.problem_text
    )
    row.gaps = [
        "observation_space is empty",
        "action_space is empty",
        "reward_spec is empty",
        "approach is empty",
    ]
    session.add(row)
    session.commit()
    session.refresh(row)
    return _spec_out(row)


@router.get("/specifications/{spec_id}")
def get_specification(spec_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(RLProblemSpecification, spec_id)
    if row is None:
        raise _not_found("specification")
    return _spec_out(row)


@router.post("/specifications/{spec_id}/formalize")
def formalize_specification(
    spec_id: str, payload: dict, session: Session = Depends(get_db)
) -> dict:
    """Run the Architect's deterministic formalisation on a spec."""
    row = session.get(RLProblemSpecification, spec_id)
    if row is None:
        raise _not_found("specification")
    formal = tool_registry.run_tool(
        session, "FormalizeRLProblem", {"gym_id": payload.get("gym_id", "CartPole-v1")}
    )
    row.observation_space = formal["observation_space"]
    row.action_space = formal["action_space"]
    row.episode_structure = formal["episode_structure"]
    row.reward_spec = formal["reward_spec"]
    approach = tool_registry.run_tool(
        session, "SelectRLApproach", {"gym_id": payload.get("gym_id", "CartPole-v1")}
    )
    row.approach = approach
    gaps = tool_registry.run_tool(
        session, "DetectSpecificationGaps", {"specification_id": row.id}
    )["gaps"]
    row.gaps = gaps
    row.status = "reviewed" if not gaps else "draft"
    session.commit()
    return _spec_out(row)


# ---------------------------------------------------------------------------
# Environments (Environment Factory)
# ---------------------------------------------------------------------------


@router.get("/environments")
def list_environments(session: Session = Depends(get_db)) -> list[dict]:
    rows = session.query(Environment).order_by(Environment.created_at).all()
    return [_env_out(row) for row in rows]


@router.post("/environments", status_code=201)
def create_environment(payload: EnvironmentCreate, session: Session = Depends(get_db)) -> dict:
    project = session.get(Project, payload.project_id)
    if project is None:
        raise _not_found("project")
    result = tool_registry.run_tool(
        session,
        "GenerateEnvironment",
        {
            "project_id": payload.project_id,
            "name": payload.name,
            "gym_id": payload.gym_id,
        },
    )
    row = session.get(Environment, result["environment_id"])
    if payload.specification_id:
        row.specification_id = payload.specification_id
    if payload.config:
        row.config = {**(row.config or {}), **payload.config}
    session.commit()
    return _env_out(row)


@router.get("/environments/{env_id}")
def get_environment(env_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Environment, env_id)
    if row is None:
        raise _not_found("environment")
    return _env_out(row)


@router.post("/environments/validate", response_model=EnvironmentValidationOut)
def validate_environment(payload: dict) -> dict:
    """Validate any gym id (no DB row needed): check_env + smoke episode."""
    gym_id = payload.get("gym_id", "CartPole-v1")
    return rl.validate_environment(gym_id, seed=payload.get("seed", 0))


# ---------------------------------------------------------------------------
# Experiments / training (Experiment Factory)
# ---------------------------------------------------------------------------


@router.post("/experiments", status_code=201)
def create_experiment(payload: ExperimentCreate, session: Session = Depends(get_db)) -> dict:
    project = session.get(Project, payload.project_id)
    if project is None:
        raise _not_found("project")
    environment = session.get(Environment, payload.environment_id)
    if environment is None:
        raise _not_found("environment")
    config = payload.config
    row = Experiment(
        project_id=payload.project_id,
        environment_id=payload.environment_id,
        specification_id=payload.specification_id,
        name=payload.name,
        algorithm=payload.algorithm,
        config=config.model_dump(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _experiment_out(row)


@router.get("/experiments")
def list_experiments(
    project_id: str | None = None, session: Session = Depends(get_db)
) -> list[dict]:
    """List experiments (Phase 7), optionally filtered by project."""
    query = session.query(Experiment).order_by(Experiment.created_at)
    if project_id is not None:
        query = query.filter(Experiment.project_id == project_id)
    return [_experiment_out(row) for row in query.all()]


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    return _experiment_out(row)


@router.post("/experiments/{experiment_id}/train", status_code=202)
def train_experiment(
    experiment_id: str, payload: TrainRequest, session: Session = Depends(get_db)
) -> dict:
    """Enqueue PPO training. Never runs training in the request."""
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    config = payload.config or TrainingConfig(**(row.config or {}))
    run = TrainingRun(
        experiment_id=row.id, status="queued", total_timesteps=config.total_timesteps
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    job = queue.enqueue(
        session,
        kind="train",
        payload={"experiment_id": row.id, "training_run_id": run.id, "config": config.model_dump()},
    )
    run.job_id = job.id
    row.status = "training_queued"
    session.commit()
    return {
        "experiment_id": row.id,
        "training_run_id": run.id,
        "job_id": job.id,
        "status": job.status,
    }


@router.post("/experiments/{experiment_id}/baseline", status_code=202)
def baseline_experiment(
    experiment_id: str, payload: dict, session: Session = Depends(get_db)
) -> dict:
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    job = queue.enqueue(
        session,
        kind="baseline",
        payload={
            "experiment_id": row.id,
            "config": row.config or {},
            "episodes": payload.get("episodes", 20),
            "seed": payload.get("seed", 0),
        },
    )
    return {"experiment_id": row.id, "job_id": job.id, "status": job.status}


@router.get("/experiments/{experiment_id}/metrics", response_model=MetricsOut)
def experiment_metrics(experiment_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    run = (
        session.query(TrainingRun)
        .filter(TrainingRun.experiment_id == experiment_id)
        .order_by(TrainingRun.created_at.desc())
        .first()
    )
    if run is None:
        return {
            "experiment_id": experiment_id,
            "training_run_id": None,
            "status": "no_run",
            "current_step": 0,
            "total_timesteps": 0,
            "metrics": {},
        }
    return {
        "experiment_id": experiment_id,
        "training_run_id": run.id,
        "status": run.status,
        "current_step": run.current_step,
        "total_timesteps": run.total_timesteps,
        "metrics": run.metrics or {},
    }


@router.get("/experiments/{experiment_id}/history")
def experiment_history(experiment_id: str, session: Session = Depends(get_db)) -> dict:
    """Training history (Phase 7): the persisted metrics.csv rows of the
    latest training run — timestep / mean episode reward points.

    The history is read from artifact storage (the metrics.csv the
    worker wrote at training time), not recomputed or invented.
    """
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    run = (
        session.query(TrainingRun)
        .filter(TrainingRun.experiment_id == experiment_id)
        .order_by(TrainingRun.created_at.desc())
        .first()
    )
    if run is None:
        return {
            "experiment_id": experiment_id,
            "training_run_id": None,
            "status": "no_run",
            "points": [],
        }
    key = f"training/{experiment_id}/{run.id}/metrics.csv"
    storage = LocalStorage()
    if not storage.exists(key):
        return {
            "experiment_id": experiment_id,
            "training_run_id": run.id,
            "status": run.status,
            "points": [],
        }
    points = []
    for record in csv.DictReader(io.StringIO(storage.get(key).decode())):
        raw = (record.get("mean_episode_reward") or "").strip()
        points.append(
            {
                "timestep": int(record["timestep"]),
                "mean_episode_reward": float(raw) if raw else None,
            }
        )
    return {
        "experiment_id": experiment_id,
        "training_run_id": run.id,
        "status": run.status,
        "points": points,
    }


@router.get("/experiments/{experiment_id}/events")
async def experiment_events(experiment_id: str) -> StreamingResponse:
    """SSE: live training progress for an experiment (polls DB rows)."""

    async def _generate():
        seen_step = -1
        for _ in range(120):  # up to ~60 s of polling
            session = SessionLocal()
            try:
                run = (
                    session.query(TrainingRun)
                    .filter(TrainingRun.experiment_id == experiment_id)
                    .order_by(TrainingRun.created_at.desc())
                    .first()
                )
                if run is not None and run.current_step != seen_step:
                    seen_step = run.current_step
                    payload = {
                        "training_run_id": run.id,
                        "status": run.status,
                        "current_step": run.current_step,
                        "total_timesteps": run.total_timesteps,
                        "metrics": run.metrics or {},
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                    if run.status in ("completed", "failed", "cancelled"):
                        return
                elif run is None:
                    yield f"data: {json.dumps({'status': 'no_run'})}\n\n"
                    return
            finally:
                session.close()
            await asyncio.sleep(0.5)

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("/experiments/{experiment_id}/evaluate", status_code=202)
def evaluate_experiment(
    experiment_id: str, payload: EvaluateRequest, session: Session = Depends(get_db)
) -> dict:
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    eval_run = EvaluationRun(experiment_id=row.id, policy_id=payload.policy_id, status="queued")
    session.add(eval_run)
    session.commit()
    session.refresh(eval_run)
    job = queue.enqueue(
        session,
        kind="evaluate",
        payload={
            "experiment_id": row.id,
            "evaluation_run_id": eval_run.id,
            "policy_id": payload.policy_id,
            "episodes": payload.episodes,
            "seed": payload.seed,
            "deterministic": payload.deterministic,
        },
    )
    return {"evaluation_run_id": eval_run.id, "job_id": job.id, "status": job.status}


# ---------------------------------------------------------------------------
# Evaluations
# ---------------------------------------------------------------------------


@router.get("/evaluations")
def list_evaluations(
    experiment_id: str | None = None, session: Session = Depends(get_db)
) -> list[dict]:
    """List evaluation runs (Phase 7), optionally filtered by experiment."""
    query = session.query(EvaluationRun).order_by(EvaluationRun.created_at)
    if experiment_id is not None:
        query = query.filter(EvaluationRun.experiment_id == experiment_id)
    return [_evaluation_out(row) for row in query.all()]


@router.get("/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(EvaluationRun, evaluation_id)
    if row is None:
        raise _not_found("evaluation")
    return _evaluation_out(row)


@router.get("/evaluations/{evaluation_id}/report")
def get_evaluation_report(evaluation_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(EvaluationRun, evaluation_id)
    if row is None:
        raise _not_found("evaluation")
    return tool_registry.run_tool(
        session, "GenerateEvaluationReport", {"evaluation_run_id": row.id}
    )


# ---------------------------------------------------------------------------
# Checkpoints / policies / export (Deployment Factory)
# ---------------------------------------------------------------------------


@router.get("/experiments/{experiment_id}/checkpoints")
def list_checkpoints(experiment_id: str, session: Session = Depends(get_db)) -> list[dict]:
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise _not_found("experiment")
    return [
        {"id": c.id, "step": c.step, "artifact_id": c.artifact_id, "created_at": _iso(c.created_at)}
        for c in session.query(Checkpoint).filter(Checkpoint.experiment_id == experiment_id).all()
    ]


@router.post("/policies", status_code=201)
def create_policy(payload: dict, session: Session = Depends(get_db)) -> dict:
    experiment = session.get(Experiment, payload.get("experiment_id"))
    if experiment is None:
        raise _not_found("experiment")
    checkpoint_id = payload.get("checkpoint_id")
    if checkpoint_id:
        checkpoint = session.get(Checkpoint, checkpoint_id)
        if checkpoint is None:
            raise _not_found("checkpoint")
    else:
        checkpoint = (
            session.query(Checkpoint)
            .filter(Checkpoint.experiment_id == experiment.id)
            .order_by(Checkpoint.step.desc())
            .first()
        )
        if checkpoint is None:
            raise HTTPException(
                status_code=409, detail="no checkpoint exists for this experiment yet"
            )
        checkpoint_id = checkpoint.id
    policy = Policy(
        experiment_id=experiment.id,
        checkpoint_id=checkpoint_id,
        name=payload.get("name", f"{experiment.name}-policy"),
        algorithm=experiment.algorithm,
        artifact_id=checkpoint.artifact_id,
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return {
        "id": policy.id,
        "experiment_id": policy.experiment_id,
        "checkpoint_id": policy.checkpoint_id,
        "name": policy.name,
        "algorithm": policy.algorithm,
        "artifact_id": policy.artifact_id,
        "status": policy.status,
        "manifest": policy.manifest or {},
    }


@router.get("/policies/{policy_id}")
def get_policy(policy_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Policy, policy_id)
    if row is None:
        raise _not_found("policy")
    return {
        "id": row.id,
        "experiment_id": row.experiment_id,
        "checkpoint_id": row.checkpoint_id,
        "name": row.name,
        "algorithm": row.algorithm,
        "artifact_id": row.artifact_id,
        "status": row.status,
        "manifest": row.manifest or {},
    }


@router.post("/policies/{policy_id}/export", status_code=202)
def export_policy(policy_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Policy, policy_id)
    if row is None:
        raise _not_found("policy")
    job = queue.enqueue(session, kind="export", payload={"policy_id": row.id})
    return {"policy_id": row.id, "job_id": job.id, "status": job.status}


# ---------------------------------------------------------------------------
# Episodes
# ---------------------------------------------------------------------------


@router.get("/episodes")
def list_episodes(
    environment_id: str | None = None, session: Session = Depends(get_db)
) -> list[dict]:
    """List recorded episodes (Phase 7), optionally by environment."""
    query = session.query(Episode).order_by(Episode.created_at)
    if environment_id is not None:
        query = query.filter(Episode.environment_id == environment_id)
    return [_episode_out(row) for row in query.all()]


@router.get("/episodes/{episode_id}")
def get_episode(episode_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Episode, episode_id)
    if row is None:
        raise _not_found("episode")
    return _episode_out(row)


@router.get("/episodes/{episode_id}/trace")
def get_episode_trace(episode_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Episode, episode_id)
    if row is None:
        raise _not_found("episode")
    if not row.trace_artifact_id:
        raise HTTPException(status_code=404, detail="episode has no recorded trace")
    artifact = session.get(Artifact, row.trace_artifact_id)
    if artifact is None:
        raise _not_found("artifact")
    data = json.loads(resolve_local_path(artifact.storage_uri).read_text())
    return {"episode_id": row.id, **data}


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Artifact, artifact_id)
    if row is None:
        raise _not_found("artifact")
    return {
        "id": row.id,
        "kind": row.kind,
        "name": row.name,
        "storage_uri": row.storage_uri,
        "size_bytes": row.size_bytes,
        "sha256": row.sha256,
        "metadata": row.artifact_metadata or {},
    }


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: str, session: Session = Depends(get_db)) -> Response:
    """Download an artifact's bytes (Phase 7, e.g. the delivery package
    zip). Local storage only; non-local URIs answer 501. The path is
    resolved through the traversal-guarded ``resolve_local_path``."""
    row = session.get(Artifact, artifact_id)
    if row is None:
        raise _not_found("artifact")
    try:
        path = resolve_local_path(row.storage_uri)
    except ValueError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"artifact storage is not local: {row.storage_uri}",
        ) from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact bytes not found in storage")
    return Response(
        content=path.read_bytes(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{row.name}"'},
    )


# ---------------------------------------------------------------------------
# Capabilities / tools
# ---------------------------------------------------------------------------


@router.get("/capabilities/tools")
def list_tools() -> list[dict]:
    return tool_registry.list_definitions()


@router.post("/capabilities/tools/{name}/run")
def run_tool_endpoint(name: str, payload: dict, session: Session = Depends(get_db)) -> dict:
    try:
        return tool_registry.run_tool(session, name, payload or {})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


@router.post("/capabilities/seed-tools")
def seed_tools(session: Session = Depends(get_db)) -> dict:
    count = tool_registry.seed_tool_definitions(session)
    return {"seeded": count}


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}")
def get_job(job_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Job, job_id)
    if row is None:
        raise _not_found("job")
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "retry_count": row.retry_count,
        "result": row.result or {},
        "error": row.error,
    }


@router.post("/jobs/{job_id}/cancel")
def cancel_job_endpoint(job_id: str, session: Session = Depends(get_db)) -> dict:
    row = queue.cancel_job(session, job_id=job_id)
    if row is None:
        raise _not_found("job")
    return {"id": row.id, "status": row.status}


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------


@router.post("/workflows", status_code=201)
def create_workflow(payload: dict, session: Session = Depends(get_db)) -> dict:
    project = session.get(Project, payload.get("project_id"))
    if project is None:
        raise _not_found("project")
    workflow = Workflow(
        project_id=payload["project_id"],
        name=payload.get("name", "training-workflow"),
        kind=payload.get("kind", "training"),
        definition=payload.get("definition", {}),
    )
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    return {
        "id": workflow.id,
        "project_id": workflow.project_id,
        "name": workflow.name,
        "kind": workflow.kind,
        "status": workflow.status,
    }


@router.post("/workflows/{workflow_id}/run", status_code=202)
def run_workflow(workflow_id: str, payload: dict, session: Session = Depends(get_db)) -> dict:
    from .workflows import run_training_workflow

    workflow = session.get(Workflow, workflow_id)
    if workflow is None:
        raise _not_found("workflow")
    execution = WorkflowExecution(workflow_id=workflow.id, status="created")
    session.add(execution)
    session.commit()
    session.refresh(execution)
    result = run_training_workflow(
        session,
        workflow_execution_id=execution.id,
        project_id=workflow.project_id,
        environment_id=payload["environment_id"],
        name=payload.get("name", "workflow-experiment"),
        config=TrainingConfig(**payload.get("config", {})) if payload.get("config") else None,
    )
    return result


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Workflow, workflow_id)
    if row is None:
        raise _not_found("workflow")
    executions = (
        session.query(WorkflowExecution)
        .filter(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.created_at.desc())
        .all()
    )
    return {
        "id": row.id,
        "project_id": row.project_id,
        "name": row.name,
        "kind": row.kind,
        "status": row.status,
        "executions": [
            {
                "id": e.id,
                "status": e.status,
                "state": e.state or {},
                "langgraph_thread_id": e.langgraph_thread_id,
            }
            for e in executions
        ],
    }


@router.post("/workflows/{workflow_id}/cancel")
def cancel_workflow(workflow_id: str, session: Session = Depends(get_db)) -> dict:
    row = session.get(Workflow, workflow_id)
    if row is None:
        raise _not_found("workflow")
    row.status = "cancelled"
    for execution in session.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_id,
        WorkflowExecution.status.in_(("created", "running")),
    ):
        execution.status = "cancelled"
        execution.finished_at = utcnow()
    session.commit()
    return {"id": row.id, "status": row.status}


# ---------------------------------------------------------------------------
# Workers / providers / events
# ---------------------------------------------------------------------------


@router.get("/workers")
def list_workers(session: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": w.id,
            "name": w.name,
            "status": w.status,
            "last_heartbeat_at": _iso(w.last_heartbeat_at),
        }
        for w in session.query(Worker).order_by(Worker.created_at).all()
    ]


@router.get("/events")
async def stream_events(session: Session = Depends(get_db)) -> StreamingResponse:
    """SSE: recent audit/provenance events, then the stream closes."""
    rows = (
        session.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100).all()
    )

    async def _generate():
        for row in reversed(rows):
            yield (
                "data: "
                + json.dumps(
                    {
                        "id": row.id,
                        "actor": row.actor,
                        "action": row.action,
                        "entity_type": row.entity_type,
                        "entity_id": row.entity_id,
                        "details": row.details or {},
                        "created_at": _iso(row.created_at),
                    }
                )
                + "\n\n"
            )

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.get("/evaluation-suites")
def list_evaluation_suites(session: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": s.id, "project_id": s.project_id, "name": s.name, "criteria": s.criteria or {}}
        for s in session.query(EvaluationSuite).order_by(EvaluationSuite.created_at).all()
    ]
