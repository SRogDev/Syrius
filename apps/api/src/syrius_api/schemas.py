"""Pydantic request/response schemas for the Syrius API (Phases 1–6).

Runtime validation only — the SQLAlchemy models in ``models.py`` are the
persistence layer. Defaults for training are the plan §10.2 CartPole
reference config, exactly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Training config (plan §10.2 — CartPole reference, editable + versioned)
# ---------------------------------------------------------------------------


class TrainingConfig(BaseModel):
    env_id: str = "CartPole-v1"
    algorithm: str = "PPO"
    seed: int = 42
    total_timesteps: int = 20000
    learning_rate: float = 0.0003
    n_steps: int = 2048
    batch_size: int = 64
    n_epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    eval_episodes: int = 20
    eval_deterministic: bool = True
    eval_seed: int = 100
    version: int = 1


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str = ""
    workspace_id: str | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    status: str
    workspace_id: str | None = None


# ---------------------------------------------------------------------------
# RL problem specifications (Architect)
# ---------------------------------------------------------------------------


class SpecificationCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=256)
    problem_text: str = ""


class SpecificationOut(BaseModel):
    id: str
    project_id: str
    title: str
    problem_text: str
    observation_space: dict = {}
    action_space: dict = {}
    episode_structure: dict = {}
    constraints: dict = {}
    reward_spec: dict = {}
    approach: dict = {}
    status: str
    gaps: list = []
    version: int


# ---------------------------------------------------------------------------
# Environments
# ---------------------------------------------------------------------------


class EnvironmentCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=1, max_length=256)
    gym_id: str = "CartPole-v1"
    specification_id: str | None = None
    config: dict = {}


class EnvironmentOut(BaseModel):
    id: str
    project_id: str
    name: str
    gym_id: str
    version: int
    config: dict = {}
    status: str


class EnvironmentValidationOut(BaseModel):
    gym_id: str
    valid: bool
    observation_space: dict
    action_space: dict
    smoke_episode_length: int
    smoke_episode_reward: float
    warnings: list[str] = []
    checked_with: str = "gymnasium.check_env"


# ---------------------------------------------------------------------------
# Experiments / training
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    project_id: str
    environment_id: str
    name: str = Field(min_length=1, max_length=256)
    specification_id: str | None = None
    algorithm: str = "PPO"
    config: TrainingConfig = Field(default_factory=TrainingConfig)


class ExperimentOut(BaseModel):
    id: str
    project_id: str
    environment_id: str
    name: str
    algorithm: str
    config: dict = {}
    status: str


class TrainRequest(BaseModel):
    config: TrainingConfig | None = None


class MetricsOut(BaseModel):
    experiment_id: str
    training_run_id: str | None = None
    status: str
    current_step: int = 0
    total_timesteps: int = 0
    metrics: dict = {}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class EvaluateRequest(BaseModel):
    policy_id: str | None = None
    episodes: int = 20
    seed: int = 100
    deterministic: bool = True


class EvaluationOut(BaseModel):
    id: str
    experiment_id: str
    policy_id: str | None = None
    status: str
    metrics: dict = {}


# ---------------------------------------------------------------------------
# Episodes / policies / workflows / workers / events
# ---------------------------------------------------------------------------


class EpisodeOut(BaseModel):
    id: str
    environment_id: str
    length: int
    total_reward: float
    success: bool | None = None
    seed: int
    trace_artifact_id: str | None = None


class PolicyExportOut(BaseModel):
    policy_id: str
    artifact_id: str
    storage_uri: str
    manifest: dict = {}
    validation: dict = {}


class WorkflowOut(BaseModel):
    id: str
    project_id: str
    name: str
    kind: str
    status: str


class WorkerOut(BaseModel):
    id: str
    name: str
    status: str
    last_heartbeat_at: str | None = None


class AuditEventOut(BaseModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: dict = {}
    created_at: str


class JobOut(BaseModel):
    id: str
    kind: str
    status: str
    retry_count: int
    result: dict = {}
    error: str | None = None
