"""Core domain models — Syrius Phases 1, 2, 3, 4, 6 (plan §12).

Every entity the CartPole slice needs is a real table; entities the slice
does not use yet are NOT created as empty files — they are listed as
Not started in IMPLEMENTATION_STATUS.md. IDs are UUID strings so rows
are addressable identically on PostgreSQL and SQLite. Flexible
structured data (configs, hyperparams, metrics, manifests) lives in JSON
columns — JSONB on Postgres, TEXT-backed JSON on SQLite — never in
untyped text blobs.

Timestamps are UTC. ``created_at``/``updated_at`` use ``func.now()``
server defaults on Postgres; SQLite fills them from the Python-side
defaults below so both backends agree.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class _Timestamped(Base):
    """Shared created/updated timestamps (abstract)."""

    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Workspace(_Timestamped):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(256), nullable=False)


class User(_Timestamped):
    """Minimal user row. Auth is out of scope for v0.1; this is identity
    for ownership/provenance only, never credentials."""

    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, default="")


class Project(_Timestamped):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=True
    )
    owner_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class RLProblemSpecification(_Timestamped):
    """Formalised RL problem spec (Phase 2, Architect output)."""

    __tablename__ = "rl_problem_specifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    problem_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    observation_space: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    action_space: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    episode_structure: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    constraints: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reward_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    approach: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    gaps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Environment(_Timestamped):
    __tablename__ = "environments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    specification_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rl_problem_specifications.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    gym_id: Mapped[str] = mapped_column(String(128), nullable=False, default="CartPole-v1")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")


class Scenario(_Timestamped):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    environment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("environments.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class Artifact(_Timestamped):
    """A stored blob (checkpoint, trace, report, package). The DB row is
    the pointer; bytes live in artifact storage, never in Postgres."""

    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    artifact_metadata: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )


class Episode(_Timestamped):
    """One recorded episode. The step-by-step trace lives in artifact
    storage (``trace_artifact_id``); only aggregates live in this row."""

    __tablename__ = "episodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    environment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("environments.id"), nullable=False
    )
    scenario_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scenarios.id"), nullable=True
    )
    policy_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("policies.id"), nullable=True
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    trace_artifact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("artifacts.id"), nullable=True
    )


class Experiment(_Timestamped):
    __tablename__ = "experiments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    environment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("environments.id"), nullable=False
    )
    specification_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rl_problem_specifications.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, default="PPO")
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")


class TrainingRun(_Timestamped):
    __tablename__ = "training_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False
    )
    job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("jobs.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    total_timesteps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Checkpoint(_Timestamped):
    __tablename__ = "checkpoints"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False
    )
    training_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("training_runs.id"), nullable=True
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifacts.id"), nullable=False
    )


class Policy(_Timestamped):
    __tablename__ = "policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False
    )
    checkpoint_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("checkpoints.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, default="PPO")
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    artifact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("artifacts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")


class EvaluationSuite(_Timestamped):
    __tablename__ = "evaluation_suites"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class EvaluationRun(_Timestamped):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    evaluation_suite_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evaluation_suites.id"), nullable=True
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False
    )
    policy_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("policies.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EvaluationResult(_Timestamped):
    __tablename__ = "evaluation_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    evaluation_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id"), nullable=False
    )
    episode_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("episodes.id"), nullable=True
    )
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class ToolDefinition(_Timestamped):
    """Registered capability tool (plan §7.3). Definitions are seeded
    from the code registry; execution lives in the tool handlers, never
    as arbitrary shell/Python execution."""

    __tablename__ = "tool_definitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    input_schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not_implemented"
    )


class Workflow(_Timestamped):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="training")
    definition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")


class WorkflowExecution(_Timestamped):
    """One workflow run. ``state`` is the persisted LangGraph-compatible
    checkpoint state (thread id + step values as plain JSON)."""

    __tablename__ = "workflow_executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    langgraph_thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Job(_Timestamped):
    """Postgres-backed job queue entry (plan §8.2)."""

    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    leased_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    logs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workers.id"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Worker(_Timestamped):
    __tablename__ = "workers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    capabilities: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class WorkerRegistration(_Timestamped):
    """Phase 0 table (migration 0001); kept as a model so Alembic
    metadata covers the whole schema from 0002 on."""

    __tablename__ = "worker_registrations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="alive")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ProviderConnection(_Timestamped):
    """BYOK provider connection. Stores a *reference* to the credential
    (``secret_ref``), never the secret itself."""

    __tablename__ = "provider_connections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="byok")
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    secret_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor: Mapped[str] = mapped_column(String(256), nullable=False, default="system")
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


def record_audit(
    session,
    *,
    actor: str = "system",
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> AuditEvent:
    """Append one provenance/audit event to *session* (caller commits)."""
    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    session.add(event)
    return event
