"""Core domain migration (Phases 1, 2, 3, 4, 6): all §12 entities the
CartPole slice needs. Matches ``syrius_api.models.Base.metadata``.
PostgreSQL is canonical; the same models are used with SQLite locally
(via ``Base.metadata.create_all`` in tests/dev).
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _ts_columns():
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        *_ts_columns(),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False, server_default=""),
        *_ts_columns(),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        *_ts_columns(),
    )
    op.create_table(
        "rl_problem_specifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("problem_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("observation_space", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("action_space", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("episode_structure", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("constraints", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("reward_spec", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("approach", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("gaps", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        *_ts_columns(),
    )
    op.create_table(
        "environments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "specification_id",
            sa.String(36),
            sa.ForeignKey("rl_problem_specifications.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("gym_id", sa.String(128), nullable=False, server_default="CartPole-v1"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        *_ts_columns(),
    )
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "environment_id", sa.String(36), sa.ForeignKey("environments.id"), nullable=False
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        *_ts_columns(),
    )
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("storage_uri", sa.String(1024), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        *_ts_columns(),
    )
    op.create_table(
        "workers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=False, server_default="{}"),
        *_ts_columns(),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("lease_owner", sa.String(128), nullable=True),
        sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("logs", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.String(36), sa.ForeignKey("workers.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_columns(),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "environment_id", sa.String(36), sa.ForeignKey("environments.id"), nullable=False
        ),
        sa.Column(
            "specification_id",
            sa.String(36),
            sa.ForeignKey("rl_problem_specifications.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("algorithm", sa.String(64), nullable=False, server_default="PPO"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        *_ts_columns(),
    )
    op.create_table(
        "training_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("total_timesteps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_columns(),
    )
    op.create_table(
        "checkpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column(
            "training_run_id", sa.String(36), sa.ForeignKey("training_runs.id"), nullable=True
        ),
        sa.Column("step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("artifact_id", sa.String(36), sa.ForeignKey("artifacts.id"), nullable=False),
        *_ts_columns(),
    )
    op.create_table(
        "policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("checkpoint_id", sa.String(36), sa.ForeignKey("checkpoints.id"), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("algorithm", sa.String(64), nullable=False, server_default="PPO"),
        sa.Column("manifest", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("artifact_id", sa.String(36), sa.ForeignKey("artifacts.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        *_ts_columns(),
    )
    op.create_table(
        "episodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "environment_id", sa.String(36), sa.ForeignKey("environments.id"), nullable=False
        ),
        sa.Column("scenario_id", sa.String(36), sa.ForeignKey("scenarios.id"), nullable=True),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id"), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_reward", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("trace_artifact_id", sa.String(36), sa.ForeignKey("artifacts.id"), nullable=True),
        *_ts_columns(),
    )
    op.create_table(
        "evaluation_suites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False, server_default="{}"),
        *_ts_columns(),
    )
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "evaluation_suite_id",
            sa.String(36),
            sa.ForeignKey("evaluation_suites.id"),
            nullable=True,
        ),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_columns(),
    )
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "evaluation_run_id", sa.String(36), sa.ForeignKey("evaluation_runs.id"), nullable=False
        ),
        sa.Column("episode_id", sa.String(36), sa.ForeignKey("episodes.id"), nullable=True),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        *_ts_columns(),
    )
    op.create_table(
        "tool_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("department", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("input_schema", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("output_schema", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="not_implemented"),
        *_ts_columns(),
    )
    op.create_table(
        "workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False, server_default="training"),
        sa.Column("definition", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        *_ts_columns(),
    )
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("state", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("langgraph_thread_id", sa.String(128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_columns(),
    )
    op.create_table(
        "provider_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("provider", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, server_default="byok"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("secret_ref", sa.String(256), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        *_ts_columns(),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor", sa.String(256), nullable=False, server_default="system"),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    for table in [
        "audit_events",
        "provider_connections",
        "workflow_executions",
        "workflows",
        "tool_definitions",
        "evaluation_results",
        "evaluation_runs",
        "evaluation_suites",
        "episodes",
        "policies",
        "checkpoints",
        "training_runs",
        "experiments",
        "jobs",
        "workers",
        "artifacts",
        "scenarios",
        "environments",
        "rl_problem_specifications",
        "projects",
        "users",
        "workspaces",
    ]:
        op.drop_table(table)
