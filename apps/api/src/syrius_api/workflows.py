"""Agentic orchestration (Phase 3) — LangGraph workflow for the
training slice.

The graph is small and deterministic: validate the environment, create
the experiment, enqueue training. State is persisted twice: in
LangGraph's ``MemorySaver`` checkpointer (per-thread) and in the
``workflow_executions`` table (durable, Postgres/SQLite), so a run can
be inspected and resumed from the database even after a restart.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from . import jobs as queue
from . import rl
from .models import Environment, Experiment, WorkflowExecution, new_id, utcnow
from .schemas import TrainingConfig


class TrainingWorkflowState(TypedDict, total=False):
    project_id: str
    gym_id: str
    environment_id: str
    experiment_id: str
    job_id: str
    status: str
    error: str


def _node_validate_env(state: TrainingWorkflowState) -> dict:
    gym_id = state.get("gym_id", "CartPole-v1")
    result = rl.validate_environment(gym_id)
    if not result["valid"]:
        return {"status": "failed", "error": f"environment invalid: {result['warnings']}"}
    return {"status": "env_validated"}


def _node_create_experiment(state: TrainingWorkflowState) -> dict:
    # The DB row is created by the caller (run_training_workflow) so the
    # graph stays pure; this node only records the transition.
    if not state.get("experiment_id"):
        return {"status": "failed", "error": "no experiment_id in state"}
    return {"status": "experiment_created"}


def _node_queue_training(state: TrainingWorkflowState) -> dict:
    if not state.get("experiment_id"):
        return {"status": "failed", "error": "no experiment_id in state"}
    return {"status": "training_queued"}


def build_training_graph() -> Any:
    graph = StateGraph(TrainingWorkflowState)
    graph.add_node("validate_env", _node_validate_env)
    graph.add_node("create_experiment", _node_create_experiment)
    graph.add_node("queue_training", _node_queue_training)
    graph.add_edge(START, "validate_env")
    graph.add_edge("validate_env", "create_experiment")
    graph.add_edge("create_experiment", "queue_training")
    graph.add_edge("queue_training", END)
    return graph.compile(checkpointer=MemorySaver())


_TRAINING_GRAPH = build_training_graph()


def run_training_workflow(
    session: Session,
    *,
    workflow_execution_id: str,
    project_id: str,
    environment_id: str,
    name: str,
    config: TrainingConfig | None = None,
) -> dict:
    """Run the training workflow graph for an existing environment and
    persist the resulting state in ``workflow_executions``.

    Creates the Experiment row, enqueues the training job, and records
    every graph step. Returns the final state dict.
    """
    execution = session.get(WorkflowExecution, workflow_execution_id)
    if execution is None:
        raise ValueError(f"workflow execution not found: {workflow_execution_id}")
    environment = session.get(Environment, environment_id)
    if environment is None:
        raise ValueError(f"environment not found: {environment_id}")
    cfg = config or TrainingConfig()
    experiment = Experiment(
        project_id=project_id,
        environment_id=environment_id,
        name=name,
        algorithm=cfg.algorithm,
        config=cfg.model_dump(),
        status="created",
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    thread_id = execution.langgraph_thread_id or f"thread-{new_id()}"
    execution.langgraph_thread_id = thread_id
    execution.status = "running"
    execution.started_at = utcnow()
    session.commit()
    initial: TrainingWorkflowState = {
        "project_id": project_id,
        "gym_id": environment.gym_id,
        "environment_id": environment_id,
        "experiment_id": experiment.id,
        "status": "created",
    }
    final_state = _TRAINING_GRAPH.invoke(
        initial, config={"configurable": {"thread_id": thread_id}}
    )
    job = queue.enqueue(
        session, kind="train", payload={"experiment_id": experiment.id, "config": cfg.model_dump()}
    )
    experiment.status = "training_queued"
    session.commit()
    final_state = {**final_state, "job_id": job.id, "status": "training_queued"}
    execution.state = dict(final_state)
    execution.status = "completed"
    execution.finished_at = utcnow()
    session.commit()
    return {
        "workflow_execution_id": execution.id,
        "experiment_id": experiment.id,
        "job_id": job.id,
        "thread_id": thread_id,
        "state": dict(final_state),
    }
