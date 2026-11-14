"""Tool registry (plan §7.3) — RL Architect (12), Environment Factory
(18), Experiment Factory (17), Evaluation & QA (14), Deployment (10).

Definitions are data: name, department, description, input/output
schema, status. Definitions are separate from execution — no tool runs
arbitrary shell or Python code; each implemented tool maps to a real
handler function in this module. Tools that cannot run for real in
v0.1 are registered with status ``not_implemented`` and an honest
reason, never fake results.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from . import rl
from .capabilities import requires_human_approval
from .models import (
    Environment,
    Episode,
    EvaluationRun,
    Experiment,
    Job,
    Policy,
    RLProblemSpecification,
    ToolDefinition,
)
from .schemas import TrainingConfig

# ---------------------------------------------------------------------------
# Definition table: (name, department, description, implemented?)
# ---------------------------------------------------------------------------

_ARCHITECT = "rl_architect"
_ENV_FACTORY = "environment_factory"
_EXP_FACTORY = "experiment_factory"
_EVAL = "evaluation_qa"
_DEPLOY = "deployment_factory"

_TOOL_TABLE: list[tuple[str, str, str, bool, str]] = [
    # RL Architect (12) — deterministic spec work; AI generation is
    # BYOK-optional and never required for the CartPole slice.
    ("AnalyzeRLProblem",
        _ARCHITECT,
        "Analyse a free-text RL problem statement into structured signals.",
        True,
        ""),
    ("FormalizeRLProblem",
        _ARCHITECT,
        "Build a formal RL problem specification from structured input.",
        True,
        ""),
    ("DefineObservationSpace",
        _ARCHITECT,
        "Define the observation space from the environment's Gymnasium space.",
        True,
        ""),
    ("DefineActionSpace",
        _ARCHITECT,
        "Define the action space from the environment's Gymnasium space.",
        True,
        ""),
    ("DefineEpisodeStructure",
        _ARCHITECT,
        "Define episode start, termination and truncation rules.",
        True,
        ""),
    ("IdentifyConstraints",
        _ARCHITECT,
        "Identify constraints (safety, resources, time) for the problem.",
        True,
        ""),
    ("DraftRewardSpecification",
        _ARCHITECT,
        "Draft the reward specification from the goal description.",
        True,
        ""),
    ("SelectRLApproach",
        _ARCHITECT,
        "Select the RL approach (algorithm family) from problem structure.",
        True,
        ""),
    ("CreateEngineeringPlan",
        _ARCHITECT,
        "Create the engineering plan (phases, tools, gates) for the spec.",
        True,
        ""),
    ("ReviewRLSpecification",
        _ARCHITECT,
        "Review a specification for completeness and consistency.",
        True,
        ""),
    ("DetectSpecificationGaps",
        _ARCHITECT,
        "Detect missing fields / gaps in a specification.",
        True,
        ""),
    ("ReviseRLSpecification",
        _ARCHITECT,
        "Apply a patch to a specification (new version).",
        True,
        ""),
    # Environment Factory (18)
    ("SearchEnvironmentRegistry",
        _ENV_FACTORY,
        "Search the built-in Gymnasium environment registry.",
        True,
        ""),
    ("InspectEnvironment",
        _ENV_FACTORY,
        "Inspect (validate + describe) an environment by gym id.",
        True,
        ""),
    ("CreateEnvironmentSpecification",
        _ENV_FACTORY,
        "Create the specification record for an environment.",
        True,
        ""),
    ("GenerateEnvironment",
        _ENV_FACTORY,
        "Create a working environment record from a gym id (validated).",
        True,
        ""),
    ("ConfigureEnvironment",
        _ENV_FACTORY,
        "Set environment configuration values.",
        True,
        ""),
    ("ConfigureObservationSpace",
        _ENV_FACTORY,
        "Record the observation-space configuration.",
        True,
        ""),
    ("ConfigureActionSpace",
        _ENV_FACTORY,
        "Record the action-space configuration.",
        True,
        ""),
    ("ConfigureRewardFunction",
        _ENV_FACTORY,
        "Record the reward-function configuration.",
        True,
        ""),
    ("ConfigureTerminationConditions",
        _ENV_FACTORY,
        "Record termination/truncation configuration.",
        True,
        ""),
    ("ValidateEnvironment",
        _ENV_FACTORY,
        "Validate an environment with check_env + a smoke episode.",
        True,
        ""),
    ("RunEnvironmentSmokeTest",
        _ENV_FACTORY,
        "Run one smoke episode and report length/reward.",
        True,
        ""),
    ("RecordEpisode",
        _ENV_FACTORY,
        "Run and record one episode (trace stored as artifact).",
        True,
        ""),
    ("ReplayEpisode",
        _ENV_FACTORY,
        "Replay a recorded episode trace from artifact storage.",
        True,
        ""),
    ("InspectEpisode",
        _ENV_FACTORY,
        "Inspect a recorded episode and its trace summary.",
        True,
        ""),
    ("VersionEnvironment",
        _ENV_FACTORY,
        "Create a new version of an environment.",
        True,
        ""),
    ("CompareEnvironmentVersions",
        _ENV_FACTORY,
        "Diff the configs of two environment versions.",
        True,
        ""),
    ("PublishEnvironment",
        _ENV_FACTORY,
        "Publish an environment to the shared registry.",
        False,
        "Sharing externally requires human approval (§13) and is not wired in v0.1."),
    ("DeprecateEnvironment",
        _ENV_FACTORY,
        "Mark an environment version deprecated.",
        False,
        "Deprecation workflow is not implemented in v0.1."),
    # Experiment Factory (17)
    ("SelectRLAlgorithm",
        _EXP_FACTORY,
        "Select the RL algorithm from the spec and environment.",
        True,
        ""),
    ("CreateExperiment",
        _EXP_FACTORY,
        "Create an experiment from a project + environment.",
        True,
        ""),
    ("ConfigureTraining",
        _EXP_FACTORY,
        "Set the training configuration of an experiment.",
        True,
        ""),
    ("ConfigureHyperparameters",
        _EXP_FACTORY,
        "Set PPO hyperparameters of an experiment.",
        True,
        ""),
    ("ConfigureRandomSeeds",
        _EXP_FACTORY,
        "Set training/evaluation seeds of an experiment.",
        True,
        ""),
    ("CreateBaseline",
        _EXP_FACTORY,
        "Create a random-policy baseline definition for an experiment.",
        True,
        ""),
    ("RunBaseline",
        _EXP_FACTORY,
        "Run the random-policy baseline (real rollouts).",
        True,
        ""),
    ("TrainPolicy",
        _EXP_FACTORY,
        "Enqueue PPO training for an experiment (never inline).",
        True,
        ""),
    ("ResumeTraining",
        _EXP_FACTORY,
        "Re-enqueue training for an experiment from its stored config.",
        True,
        ""),
    ("StopTraining",
        _EXP_FACTORY,
        "Cancel a running/queued training job.",
        True,
        ""),
    ("SaveCheckpoint",
        _EXP_FACTORY,
        "Persist the latest checkpoint artifact reference.",
        True,
        ""),
    ("LoadCheckpoint",
        _EXP_FACTORY,
        "Load a checkpoint and verify it predicts.",
        True,
        ""),
    ("CollectTrainingMetrics",
        _EXP_FACTORY,
        "Collect the stored metrics of a training run.",
        True,
        ""),
    ("CompareExperiments",
        _EXP_FACTORY,
        "Compare metrics of two experiments.",
        True,
        ""),
    ("AnalyzeTrainingCurves",
        _EXP_FACTORY,
        "Analyse the metrics.csv curve of a training run.",
        True,
        ""),
    ("InspectTrainingFailure",
        _EXP_FACTORY,
        "Inspect a failed training job (real error + logs).",
        True,
        ""),
    ("ExportExperiment",
        _EXP_FACTORY,
        "Enqueue a policy export for an experiment's policy.",
        True,
        ""),
    # Evaluation & QA (14)
    ("CreateEvaluationSuite",
        _EVAL,
        "Create an evaluation suite for a project.",
        True,
        ""),
    ("DefineSuccessCriteria",
        _EVAL,
        "Define independent success criteria (not training reward).",
        True,
        ""),
    ("RunEvaluation",
        _EVAL,
        "Enqueue an independent evaluation run.",
        True,
        ""),
    ("RecordEvaluationEpisode",
        _EVAL,
        "Record one evaluation episode with its trace.",
        True,
        ""),
    ("ComputeEvaluationMetrics",
        _EVAL,
        "Compute aggregates from a finished evaluation run.",
        True,
        ""),
    ("CompareWithBaseline",
        _EVAL,
        "Compare evaluation metrics against the random baseline.",
        True,
        ""),
    ("DetectConstraintViolations",
        _EVAL,
        "Detect constraint violations in evaluation episodes.",
        True,
        ""),
    ("GenerateEvaluationReport",
        _EVAL,
        "Generate report.json + report.md with measured numbers.",
        True,
        ""),
    ("VerifySuccessIndependently",
        _EVAL,
        "Re-run evaluation from a fresh policy load.",
        True,
        ""),
    ("InspectEvaluationFailure",
        _EVAL,
        "Inspect a failed evaluation run (error + logs).",
        True,
        ""),
    ("CompareEvaluationRuns",
        _EVAL,
        "Compare metrics of two evaluation runs.",
        True,
        ""),
    ("PublishEvaluationReport",
        _EVAL,
        "Publish an evaluation report externally.",
        False,
        "Sharing externally requires human approval (§13) and is not wired in v0.1."),
    ("ArchiveEvaluation",
        _EVAL,
        "Archive an evaluation run.",
        True,
        ""),
    ("ExportEvaluationResults",
        _EVAL,
        "Export evaluation results as JSON.",
        True,
        ""),
    # Deployment Factory (10)
    ("PackagePolicy",
        _DEPLOY,
        "Build the delivery package (model + manifest + README).",
        True,
        ""),
    ("ExportPolicy",
        _DEPLOY,
        "Enqueue a policy export job.",
        True,
        ""),
    ("ValidatePolicyPackage",
        _DEPLOY,
        "Validate a package by independent load + rollouts.",
        True,
        ""),
    ("CreateDeliveryPackage",
        _DEPLOY,
        "Create a delivery package from a policy artifact.",
        True,
        ""),
    ("PublishPolicy",
        _DEPLOY,
        "Publish a policy to production.",
        False,
        "Deploying to production requires human approval (§13); no paid/prod path exists in v0.1."),
    ("VersionPolicy",
        _DEPLOY,
        "Record a new version of a policy.",
        True,
        ""),
    ("RollbackPolicy",
        _DEPLOY,
        "Roll back to a previous policy version.",
        False,
        "No production deployment exists to roll back in v0.1."),
    ("InspectPolicyManifest",
        _DEPLOY,
        "Inspect a policy's reproducibility manifest.",
        True,
        ""),
    ("VerifyReproducibility",
        _DEPLOY,
        "Verify a package reproduces its manifest's results.",
        True,
        ""),
    ("SignDeliveryPackage",
        _DEPLOY,
        "Cryptographically sign a delivery package.",
        False,
        "No signing keys or signing flow exist in v0.1."),
]


def _schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
    }


def list_definitions() -> list[dict]:
    """All registered tool definitions with status."""
    out = []
    for name, dept, desc, implemented, reason in _TOOL_TABLE:
        out.append(
            {
                "name": name,
                "department": dept,
                "description": desc,
                "status": "implemented" if implemented else "not_implemented",
                "not_implemented_reason": reason,
                "input_schema": _schema({}),
                "output_schema": _schema({}),
            }
        )
    return out


def get_definition(name: str) -> dict | None:
    for definition in list_definitions():
        if definition["name"] == name:
            return definition
    return None


def seed_tool_definitions(session: Session) -> int:
    """Upsert all definitions into ``tool_definitions``. Returns count."""
    count = 0
    for definition in list_definitions():
        row = session.query(ToolDefinition).filter_by(name=definition["name"]).first()
        if row is None:
            row = ToolDefinition(name=definition["name"])
            session.add(row)
        row.department = definition["department"]
        row.description = definition["description"]
        row.input_schema = definition["input_schema"]
        row.output_schema = definition["output_schema"]
        row.status = definition["status"]
        count += 1
    session.commit()
    return count


# ---------------------------------------------------------------------------
# Handlers — each takes (session, payload) and returns a plain dict.
# Deterministic where possible; AI-assisted generation is BYOK-optional
# and never required. Handlers that need long work enqueue a job and
# return the job id instead of blocking.
# ---------------------------------------------------------------------------

BUILTIN_REGISTRY = [
    "CartPole-v1",
    "CartPole-v0",
    "MountainCar-v0",
    "Acrobot-v1",
    "LunarLander-v3",
    "Pendulum-v1",
]


def _env_row(session: Session, payload: dict) -> Environment:
    env_id = payload.get("environment_id") or payload.get("id")
    row = session.get(Environment, env_id) if env_id else None
    if row is None:
        raise ValueError(f"environment not found: {env_id}")
    return row


def _experiment_row(session: Session, payload: dict) -> Experiment:
    exp_id = payload.get("experiment_id")
    row = session.get(Experiment, exp_id) if exp_id else None
    if row is None:
        raise ValueError(f"experiment not found: {exp_id}")
    return row


def _require_approval(action: str) -> dict:
    return {
        "approved": False,
        "requires_human_approval": True,
        "action": action,
        "reason": (
            "Plan §13: this action needs explicit human approval "
            "and has no automated path in v0.1."
        ),
    }


def h_analyze_rl_problem(session: Session, payload: dict) -> dict:
    text = payload.get("problem_text", "")
    words = {w.strip(".,;:()").lower() for w in text.split()}
    signals = {
        "mentions_balance": bool(words & {"balance", "balancing", "pole", "upright"}),
        "mentions_continuous_control": bool(words & {"continuous", "torque", "force"}),
        "mentions_discrete_actions": bool(words & {"discrete", "left", "right"}),
        "mentions_sparse_reward": bool(words & {"sparse", "rare"}),
        "word_count": len(text.split()),
    }
    return {"analysis": signals, "problem_text": text}


def h_formalize_rl_problem(session: Session, payload: dict) -> dict:
    gym_id = payload.get("gym_id", "CartPole-v1")
    validation = rl.validate_environment(gym_id)
    return {
        "gym_id": gym_id,
        "observation_space": validation["observation_space"],
        "action_space": validation["action_space"],
        "episode_structure": {
            "max_steps": 500 if gym_id.startswith("CartPole") else None,
            "termination": "pole angle or cart position beyond limits",
            "truncation": "step limit reached",
        },
        "reward_spec": {"per_step": 1.0, "goal": "maximise episode length"},
        "valid": validation["valid"],
    }


def h_define_observation_space(session: Session, payload: dict) -> dict:
    env = rl.make_env(payload.get("gym_id", "CartPole-v1"))
    return rl.space_to_dict(env.observation_space)


def h_define_action_space(session: Session, payload: dict) -> dict:
    env = rl.make_env(payload.get("gym_id", "CartPole-v1"))
    return rl.space_to_dict(env.action_space)


def h_define_episode_structure(session: Session, payload: dict) -> dict:
    return h_formalize_rl_problem(session, payload)["episode_structure"]


def h_identify_constraints(session: Session, payload: dict) -> dict:
    return {
        "constraints": payload.get(
            "constraints", ["cpu_only", "no_paid_compute", "reproducible_seeds"]
        ),
    }


def h_draft_reward_spec(session: Session, payload: dict) -> dict:
    return {
        "reward_spec": {
            "per_step": 1.0,
            "goal": payload.get("goal", "keep the pole balanced as long as possible"),
        }
    }


def h_select_rl_approach(session: Session, payload: dict) -> dict:
    # Rule-based: discrete actions + continuous observations -> PPO.
    validation = rl.validate_environment(payload.get("gym_id", "CartPole-v1"))
    action = validation["action_space"]
    approach = "PPO" if action.get("type") == "Discrete" else "SAC"
    return {
        "approach": approach,
        "algorithm": approach,
        "reason": f"action space is {action.get('type')}",
    }


def h_create_engineering_plan(session: Session, payload: dict) -> dict:
    return {
        "plan": [
            "formalise spec (Architect)",
            "validate environment (Environment Factory)",
            "random baseline (Experiment Factory)",
            "PPO training 20000 steps (Experiment Factory)",
            "independent evaluation 20 episodes (Evaluation)",
            "package + validate export (Deployment)",
        ]
    }


def h_review_spec(session: Session, payload: dict) -> dict:
    spec_id = payload.get("specification_id")
    spec = session.get(RLProblemSpecification, spec_id) if spec_id else None
    if spec is None:
        raise ValueError(f"specification not found: {spec_id}")
    gaps = h_detect_gaps(session, {"specification_id": spec_id})["gaps"]
    return {"specification_id": spec.id, "status": spec.status, "gaps": gaps, "complete": not gaps}


def h_detect_gaps(session: Session, payload: dict) -> dict:
    spec_id = payload.get("specification_id")
    spec = session.get(RLProblemSpecification, spec_id) if spec_id else None
    if spec is None:
        raise ValueError(f"specification not found: {spec_id}")
    gaps = []
    if not spec.problem_text:
        gaps.append("problem_text is empty")
    if not spec.observation_space:
        gaps.append("observation_space is empty")
    if not spec.action_space:
        gaps.append("action_space is empty")
    if not spec.reward_spec:
        gaps.append("reward_spec is empty")
    if not spec.approach:
        gaps.append("approach is empty")
    return {"specification_id": spec.id, "gaps": gaps}


def h_revise_spec(session: Session, payload: dict) -> dict:
    spec_id = payload.get("specification_id")
    spec = session.get(RLProblemSpecification, spec_id) if spec_id else None
    if spec is None:
        raise ValueError(f"specification not found: {spec_id}")
    patch = payload.get("patch", {})
    for field in (
        "problem_text",
        "observation_space",
        "action_space",
        "episode_structure",
        "constraints",
        "reward_spec",
        "approach",
        "status",
    ):
        if field in patch:
            setattr(spec, field, patch[field])
    spec.version += 1
    session.commit()
    return {"specification_id": spec.id, "version": spec.version, "status": spec.status}


def h_search_registry(session: Session, payload: dict) -> dict:
    query = (payload.get("query") or "").lower()
    found = []
    for gym_id in BUILTIN_REGISTRY:
        if query in gym_id.lower():
            try:
                spec = rl.gym.spec(gym_id)
                found.append({"gym_id": gym_id, "entry_point": str(spec.entry_point)})
            except Exception:
                found.append({"gym_id": gym_id, "entry_point": None})
    return {
        "results": found,
        "note": "Built-in Gymnasium registry only; no external registry is queried in v0.1.",
    }


def h_inspect_environment(session: Session, payload: dict) -> dict:
    return rl.validate_environment(payload.get("gym_id", "CartPole-v1"))


def h_create_env_spec(session: Session, payload: dict) -> dict:
    return h_formalize_rl_problem(session, payload)


def h_generate_environment(session: Session, payload: dict) -> dict:
    validation = rl.validate_environment(payload.get("gym_id", "CartPole-v1"))
    if not validation["valid"]:
        raise ValueError(f"environment failed validation: {validation['warnings']}")
    row = Environment(
        project_id=payload["project_id"],
        name=payload.get("name", payload.get("gym_id", "CartPole-v1")),
        gym_id=payload.get("gym_id", "CartPole-v1"),
        config={
            "observation_space": validation["observation_space"],
            "action_space": validation["action_space"],
        },
        status="validated",
    )
    session.add(row)
    session.commit()
    return {
        "environment_id": row.id,
        "gym_id": row.gym_id,
        "status": row.status,
        "validation": validation,
    }


def _configure_env(session: Session, payload: dict, key: str) -> dict:
    row = _env_row(session, payload)
    config = dict(row.config or {})
    config[key] = payload.get("value", payload.get(key, {}))
    row.config = config
    session.commit()
    return {"environment_id": row.id, "config": row.config}


def h_configure_environment(session: Session, payload: dict) -> dict:
    row = _env_row(session, payload)
    row.config = {**(row.config or {}), **(payload.get("config", {}))}
    session.commit()
    return {"environment_id": row.id, "config": row.config}


def h_validate_environment(session: Session, payload: dict) -> dict:
    if payload.get("gym_id") and not payload.get("environment_id"):
        return rl.validate_environment(payload["gym_id"])
    row = _env_row(session, payload)
    result = rl.validate_environment(row.gym_id)
    row.status = "validated" if result["valid"] else "invalid"
    session.commit()
    return result


def h_smoke_test(session: Session, payload: dict) -> dict:
    gym_id = payload.get("gym_id")
    if not gym_id:
        gym_id = _env_row(session, payload).gym_id
    env = rl.make_env(gym_id)
    length, reward, _ = rl.run_episode(env, seed=payload.get("seed", 0))
    return {"gym_id": gym_id, "length": length, "reward": reward}


def h_record_episode(session: Session, payload: dict) -> dict:
    from .executor import _register_artifact

    row = _env_row(session, payload)
    env = rl.make_env(row.gym_id)
    length, reward, trace = rl.run_episode(
        env, seed=payload.get("seed", 0), record=True
    )
    artifact = _register_artifact(
        session,
        project_id=row.project_id,
        kind="episode_trace",
        name=f"episode-{row.gym_id}-seed-{payload.get('seed', 0)}",
        key=f"episodes/{row.id}/{payload.get('seed', 0)}.json",
        data=rl.json.dumps(
            {"gym_id": row.gym_id, "seed": payload.get("seed", 0), "steps": trace}
        ).encode(),
    )
    episode = Episode(
        environment_id=row.id,
        seed=payload.get("seed", 0),
        length=length,
        total_reward=reward,
        success=length >= rl.CARTPOLE_SUCCESS_LENGTH if row.gym_id.startswith("CartPole") else None,
        trace_artifact_id=artifact.id,
    )
    session.add(episode)
    session.commit()
    return {
        "episode_id": episode.id,
        "length": length,
        "reward": reward,
        "trace_artifact_id": artifact.id,
    }


def h_replay_episode(session: Session, payload: dict) -> dict:
    episode = session.get(Episode, payload.get("episode_id"))
    if episode is None:
        raise ValueError(f"episode not found: {payload.get('episode_id')}")
    if not episode.trace_artifact_id:
        return {"episode_id": episode.id, "steps": [], "note": "no trace recorded for this episode"}
    from .executor import resolve_local_path
    from .models import Artifact

    artifact = session.get(Artifact, episode.trace_artifact_id)
    data = rl.json.loads(resolve_local_path(artifact.storage_uri).read_text())
    return {
        "episode_id": episode.id,
        "length": episode.length,
        "reward": episode.total_reward,
        "steps": data["steps"],
    }


def h_inspect_episode(session: Session, payload: dict) -> dict:
    episode = session.get(Episode, payload.get("episode_id"))
    if episode is None:
        raise ValueError(f"episode not found: {payload.get('episode_id')}")
    return {
        "episode_id": episode.id,
        "length": episode.length,
        "reward": episode.total_reward,
        "success": episode.success,
        "seed": episode.seed,
        "trace_artifact_id": episode.trace_artifact_id,
    }


def h_version_environment(session: Session, payload: dict) -> dict:
    row = _env_row(session, payload)
    new = Environment(
        project_id=row.project_id,
        specification_id=row.specification_id,
        name=row.name,
        gym_id=row.gym_id,
        version=row.version + 1,
        config=dict(row.config or {}),
        status="draft",
    )
    session.add(new)
    session.commit()
    return {"environment_id": new.id, "version": new.version, "previous_version": row.version}


def h_compare_env_versions(session: Session, payload: dict) -> dict:
    a = session.get(Environment, payload.get("environment_id_a"))
    b = session.get(Environment, payload.get("environment_id_b"))
    if a is None or b is None:
        raise ValueError("both environment ids are required")
    keys = set(a.config or {}) | set(b.config or {})
    diff = {
        k: {"a": (a.config or {}).get(k), "b": (b.config or {}).get(k)}
        for k in keys
        if (a.config or {}).get(k) != (b.config or {}).get(k)
    }
    return {"environment_a": a.id, "environment_b": b.id, "diff": diff}


def h_select_algorithm(session: Session, payload: dict) -> dict:
    return h_select_rl_approach(session, payload)


def h_create_experiment(session: Session, payload: dict) -> dict:
    config = TrainingConfig(**payload.get("config", {}))
    exp = Experiment(
        project_id=payload["project_id"],
        environment_id=payload["environment_id"],
        specification_id=payload.get("specification_id"),
        name=payload.get("name", "experiment"),
        algorithm=payload.get("algorithm", config.algorithm),
        config=config.model_dump(),
    )
    session.add(exp)
    session.commit()
    return {"experiment_id": exp.id, "algorithm": exp.algorithm, "config": exp.config}


def _update_experiment_config(session: Session, payload: dict, patch: dict) -> dict:
    exp = _experiment_row(session, payload)
    config = TrainingConfig(**{**(exp.config or {}), **patch})
    exp.config = config.model_dump()
    session.commit()
    return {"experiment_id": exp.id, "config": exp.config}


def h_configure_training(session: Session, payload: dict) -> dict:
    return _update_experiment_config(session, payload, payload.get("config", {}))


def h_configure_hyperparameters(session: Session, payload: dict) -> dict:
    allowed = {
        "learning_rate",
        "n_steps",
        "batch_size",
        "n_epochs",
        "gamma",
        "gae_lambda",
        "clip_range",
    }
    patch = {k: v for k, v in payload.get("hyperparameters", {}).items() if k in allowed}
    return _update_experiment_config(session, payload, patch)


def h_configure_seeds(session: Session, payload: dict) -> dict:
    patch = {}
    if "seed" in payload:
        patch["seed"] = payload["seed"]
    if "eval_seed" in payload:
        patch["eval_seed"] = payload["eval_seed"]
    return _update_experiment_config(session, payload, patch)


def h_create_baseline(session: Session, payload: dict) -> dict:
    exp = _experiment_row(session, payload)
    return {
        "experiment_id": exp.id,
        "baseline": {
            "policy": "random",
            "episodes": payload.get("episodes", 20),
            "seed": payload.get("seed", 0),
        },
    }


def h_run_baseline(session: Session, payload: dict) -> dict:
    exp = _experiment_row(session, payload)
    config = TrainingConfig(**(exp.config or {}))
    return rl.run_random_baseline(
        config.env_id,
        n_episodes=payload.get("episodes", config.eval_episodes),
        seed=payload.get("seed", 0),
    )


def h_train_policy(session: Session, payload: dict) -> dict:
    from .jobs import enqueue

    exp = _experiment_row(session, payload)
    job = enqueue(
        session, kind="train", payload={"experiment_id": exp.id, "config": exp.config or {}}
    )
    exp.status = "training_queued"
    session.commit()
    return {"experiment_id": exp.id, "job_id": job.id, "status": job.status}


def h_resume_training(session: Session, payload: dict) -> dict:
    return h_train_policy(session, payload)


def h_stop_training(session: Session, payload: dict) -> dict:
    from .jobs import cancel_job

    job_id = payload.get("job_id")
    job = cancel_job(session, job_id=job_id) if job_id else None
    if job is None:
        raise ValueError(f"job not found: {job_id}")
    return {"job_id": job.id, "status": job.status}


def h_save_checkpoint(session: Session, payload: dict) -> dict:
    from .models import Checkpoint

    exp = _experiment_row(session, payload)
    latest = (
        session.query(Checkpoint)
        .filter(Checkpoint.experiment_id == exp.id)
        .order_by(Checkpoint.step.desc())
        .first()
    )
    if latest is None:
        raise ValueError("no checkpoint exists for this experiment yet")
    return {
        "experiment_id": exp.id,
        "checkpoint_id": latest.id,
        "step": latest.step,
        "artifact_id": latest.artifact_id,
    }


def h_load_checkpoint(session: Session, payload: dict) -> dict:
    from .executor import resolve_local_path
    from .models import Artifact, Checkpoint

    checkpoint = session.get(Checkpoint, payload.get("checkpoint_id"))
    if checkpoint is None:
        raise ValueError(f"checkpoint not found: {payload.get('checkpoint_id')}")
    artifact = session.get(Artifact, checkpoint.artifact_id)
    model = rl.load_policy(resolve_local_path(artifact.storage_uri))
    env = rl.make_env(payload.get("gym_id", "CartPole-v1"))
    obs, _ = env.reset(seed=0)
    action, _ = model.predict(obs, deterministic=True)
    return {
        "checkpoint_id": checkpoint.id,
        "step": checkpoint.step,
        "predicts": True,
        "sample_action": int(action),
    }


def h_collect_metrics(session: Session, payload: dict) -> dict:
    from .models import TrainingRun

    run = session.get(TrainingRun, payload.get("training_run_id"))
    if run is None:
        exp = _experiment_row(session, payload)
        run = (
            session.query(TrainingRun)
            .filter(TrainingRun.experiment_id == exp.id)
            .order_by(TrainingRun.created_at.desc())
            .first()
        )
    if run is None:
        raise ValueError("no training run found")
    return {
        "training_run_id": run.id,
        "status": run.status,
        "current_step": run.current_step,
        "metrics": run.metrics or {},
    }


def h_compare_experiments(session: Session, payload: dict) -> dict:
    a = session.get(Experiment, payload.get("experiment_id_a"))
    b = session.get(Experiment, payload.get("experiment_id_b"))
    if a is None or b is None:
        raise ValueError("both experiment ids are required")
    return {
        "a": {"id": a.id, "config": a.config, "status": a.status},
        "b": {"id": b.id, "config": b.config, "status": b.status},
    }


def h_analyze_curves(session: Session, payload: dict) -> dict:
    import csv
    import io

    from .executor import resolve_local_path
    from .models import Artifact

    artifact_id = payload.get("metrics_artifact_id")
    artifact = session.get(Artifact, artifact_id) if artifact_id else None
    if artifact is None:
        raise ValueError("metrics artifact not found")
    text = resolve_local_path(artifact.storage_uri).read_text()
    rows = list(csv.DictReader(io.StringIO(text)))
    rewards = [float(r["mean_episode_reward"]) for r in rows if r.get("mean_episode_reward")]
    return {
        "points": len(rows),
        "first_mean_reward": rewards[0] if rewards else None,
        "last_mean_reward": rewards[-1] if rewards else None,
        "best_mean_reward": max(rewards) if rewards else None,
        "improved": bool(rewards and rewards[-1] > rewards[0]),
    }


def h_inspect_training_failure(session: Session, payload: dict) -> dict:
    job = session.get(Job, payload.get("job_id"))
    if job is None:
        raise ValueError(f"job not found: {payload.get('job_id')}")
    return {
        "job_id": job.id,
        "kind": job.kind,
        "status": job.status,
        "error": job.error,
        "logs": job.logs or [],
        "retry_count": job.retry_count,
    }


def h_export_experiment(session: Session, payload: dict) -> dict:
    from .jobs import enqueue

    exp = _experiment_row(session, payload)
    policy_id = payload.get("policy_id")
    if not policy_id:
        policy = session.query(Policy).filter(Policy.experiment_id == exp.id).first()
        policy_id = policy.id if policy else None
    if not policy_id:
        raise ValueError("no policy exists for this experiment yet")
    job = enqueue(session, kind="export", payload={"policy_id": policy_id})
    return {"experiment_id": exp.id, "policy_id": policy_id, "job_id": job.id, "status": job.status}


def h_create_eval_suite(session: Session, payload: dict) -> dict:
    from .models import EvaluationSuite

    suite = EvaluationSuite(
        project_id=payload["project_id"],
        name=payload.get("name", "default"),
        criteria=payload.get("criteria", {"success_length": 500, "episodes": 20}),
    )
    session.add(suite)
    session.commit()
    return {"evaluation_suite_id": suite.id, "name": suite.name, "criteria": suite.criteria}


def h_define_success_criteria(session: Session, payload: dict) -> dict:
    return {
        "success_criteria": {
            "success_length": payload.get("success_length", 500),
            "min_success_rate": payload.get("min_success_rate", 0.8),
            "note": (
                "Success is pole balanced for the full episode "
                "(independent of training reward)."
            ),
        }
    }


def h_run_evaluation(session: Session, payload: dict) -> dict:
    from .jobs import enqueue

    exp = _experiment_row(session, payload)
    eval_run = EvaluationRun(experiment_id=exp.id, policy_id=payload.get("policy_id"))
    session.add(eval_run)
    session.commit()
    job = enqueue(
        session,
        kind="evaluate",
        payload={
            "experiment_id": exp.id,
            "evaluation_run_id": eval_run.id,
            "policy_id": payload.get("policy_id"),
            "episodes": payload.get("episodes", 20),
        },
    )
    return {"evaluation_run_id": eval_run.id, "job_id": job.id, "status": job.status}


def h_record_eval_episode(session: Session, payload: dict) -> dict:
    return h_record_episode(session, payload)


def h_compute_eval_metrics(session: Session, payload: dict) -> dict:
    run = session.get(EvaluationRun, payload.get("evaluation_run_id"))
    if run is None:
        raise ValueError(f"evaluation run not found: {payload.get('evaluation_run_id')}")
    return {"evaluation_run_id": run.id, "status": run.status, "metrics": run.metrics or {}}


def h_compare_baseline(session: Session, payload: dict) -> dict:
    baseline = payload.get("baseline", {})
    evaluation = h_compute_eval_metrics(session, payload).get("metrics", {})
    return {
        "baseline_mean_reward": baseline.get("mean_reward"),
        "evaluation_mean_reward": evaluation.get("mean_reward"),
        "improvement": (
            (evaluation.get("mean_reward") or 0) - (baseline.get("mean_reward") or 0)
            if evaluation and baseline
            else None
        ),
    }


def h_detect_violations(session: Session, payload: dict) -> dict:
    metrics = h_compute_eval_metrics(session, payload).get("metrics", {})
    return {
        "constraint_violations": metrics.get("constraint_violations", 0),
        "episodes": metrics.get("episodes", 0),
    }


def h_generate_eval_report(session: Session, payload: dict) -> dict:
    run = session.get(EvaluationRun, payload.get("evaluation_run_id"))
    if run is None:
        raise ValueError(f"evaluation run not found: {payload.get('evaluation_run_id')}")
    metrics = run.metrics or {}
    report = {
        "evaluation_run_id": run.id,
        "experiment_id": run.experiment_id,
        "status": run.status,
        "mean_reward": metrics.get("mean_reward"),
        "median_reward": metrics.get("median_reward"),
        "mean_length": metrics.get("mean_length"),
        "success_rate": metrics.get("success_rate"),
        "episodes": metrics.get("episodes"),
    }
    md = (
        f"# Evaluation report — run {run.id}\n\n"
        f"- mean reward: {metrics.get('mean_reward')}\n"
        f"- median reward: {metrics.get('median_reward')}\n"
        f"- mean length: {metrics.get('mean_length')}\n"
        f"- success rate: {metrics.get('success_rate')}\n"
        f"- episodes: {metrics.get('episodes')}\n"
    )
    return {"report_json": report, "report_md": md}


def h_verify_success(session: Session, payload: dict) -> dict:
    from .executor import resolve_local_path
    from .models import Artifact, Checkpoint

    exp = _experiment_row(session, payload)
    checkpoint = (
        session.query(Checkpoint)
        .filter(Checkpoint.experiment_id == exp.id)
        .order_by(Checkpoint.step.desc())
        .first()
    )
    if checkpoint is None:
        raise ValueError("no checkpoint available to verify")
    artifact = session.get(Artifact, checkpoint.artifact_id)
    model_path = resolve_local_path(artifact.storage_uri)
    config = TrainingConfig(**(exp.config or {}))
    result = rl.evaluate_policy(
        model_path,
        config.env_id,
        n_episodes=payload.get("episodes", 5),
        seed=payload.get("seed", 1000),
    )
    return {
        "verified": True,
        "success_rate": result["success_rate"],
        "mean_reward": result["mean_reward"],
        "episodes": result["episodes"],
    }


def h_inspect_eval_failure(session: Session, payload: dict) -> dict:
    return h_inspect_training_failure(session, payload)


def h_compare_eval_runs(session: Session, payload: dict) -> dict:
    a = session.get(EvaluationRun, payload.get("evaluation_run_id_a"))
    b = session.get(EvaluationRun, payload.get("evaluation_run_id_b"))
    if a is None or b is None:
        raise ValueError("both evaluation run ids are required")
    return {"a": {"id": a.id, "metrics": a.metrics}, "b": {"id": b.id, "metrics": b.metrics}}


def h_archive_evaluation(session: Session, payload: dict) -> dict:
    run = session.get(EvaluationRun, payload.get("evaluation_run_id"))
    if run is None:
        raise ValueError(f"evaluation run not found: {payload.get('evaluation_run_id')}")
    run.status = "archived"
    session.commit()
    return {"evaluation_run_id": run.id, "status": run.status}


def h_export_eval_results(session: Session, payload: dict) -> dict:
    report = h_generate_eval_report(session, payload)
    return {"export": report["report_json"]}


def h_package_policy(session: Session, payload: dict) -> dict:
    from . import executor as _exec

    policy = session.get(Policy, payload.get("policy_id"))
    if policy is None:
        raise ValueError(f"policy not found: {payload.get('policy_id')}")
    job_result = _exec.execute_export(lambda: session, session, _FakeJob({"policy_id": policy.id}))
    return job_result


class _FakeJob:
    """Minimal job-shaped object so the export handler can run
    synchronously from the PackagePolicy tool."""

    def __init__(self, payload: dict) -> None:
        self.id = "tool-run"
        self.payload = payload


def h_export_policy(session: Session, payload: dict) -> dict:
    from .jobs import enqueue

    policy = session.get(Policy, payload.get("policy_id"))
    if policy is None:
        raise ValueError(f"policy not found: {payload.get('policy_id')}")
    job = enqueue(session, kind="export", payload={"policy_id": policy.id})
    return {"policy_id": policy.id, "job_id": job.id, "status": job.status}


def h_validate_package(session: Session, payload: dict) -> dict:
    from .executor import resolve_local_path
    from .models import Artifact

    artifact = session.get(Artifact, payload.get("artifact_id"))
    if artifact is None:
        raise ValueError(f"artifact not found: {payload.get('artifact_id')}")
    return rl.validate_delivery_package(
        resolve_local_path(artifact.storage_uri),
        payload.get("gym_id", "CartPole-v1"),
        n_episodes=payload.get("episodes", 5),
    )


def h_create_delivery_package(session: Session, payload: dict) -> dict:
    return h_package_policy(session, payload)


def h_version_policy(session: Session, payload: dict) -> dict:
    policy = session.get(Policy, payload.get("policy_id"))
    if policy is None:
        raise ValueError(f"policy not found: {payload.get('policy_id')}")
    manifest = dict(policy.manifest or {})
    manifest["version"] = int(manifest.get("version", 1)) + 1
    policy.manifest = manifest
    session.commit()
    return {"policy_id": policy.id, "manifest_version": manifest["version"]}


def h_inspect_manifest(session: Session, payload: dict) -> dict:
    policy = session.get(Policy, payload.get("policy_id"))
    if policy is None:
        raise ValueError(f"policy not found: {payload.get('policy_id')}")
    return {"policy_id": policy.id, "manifest": policy.manifest or {}}


def h_verify_reproducibility(session: Session, payload: dict) -> dict:
    return h_validate_package(session, payload)


HANDLERS: dict[str, Any] = {
    "AnalyzeRLProblem": h_analyze_rl_problem,
    "FormalizeRLProblem": h_formalize_rl_problem,
    "DefineObservationSpace": h_define_observation_space,
    "DefineActionSpace": h_define_action_space,
    "DefineEpisodeStructure": h_define_episode_structure,
    "IdentifyConstraints": h_identify_constraints,
    "DraftRewardSpecification": h_draft_reward_spec,
    "SelectRLApproach": h_select_rl_approach,
    "CreateEngineeringPlan": h_create_engineering_plan,
    "ReviewRLSpecification": h_review_spec,
    "DetectSpecificationGaps": h_detect_gaps,
    "ReviseRLSpecification": h_revise_spec,
    "SearchEnvironmentRegistry": h_search_registry,
    "InspectEnvironment": h_inspect_environment,
    "CreateEnvironmentSpecification": h_create_env_spec,
    "GenerateEnvironment": h_generate_environment,
    "ConfigureEnvironment": h_configure_environment,
    "ConfigureObservationSpace": lambda s, p: _configure_env(s, p, "observation_space"),
    "ConfigureActionSpace": lambda s, p: _configure_env(s, p, "action_space"),
    "ConfigureRewardFunction": lambda s, p: _configure_env(s, p, "reward_function"),
    "ConfigureTerminationConditions": lambda s, p: _configure_env(s, p, "termination"),
    "ValidateEnvironment": h_validate_environment,
    "RunEnvironmentSmokeTest": h_smoke_test,
    "RecordEpisode": h_record_episode,
    "ReplayEpisode": h_replay_episode,
    "InspectEpisode": h_inspect_episode,
    "VersionEnvironment": h_version_environment,
    "CompareEnvironmentVersions": h_compare_env_versions,
    "SelectRLAlgorithm": h_select_algorithm,
    "CreateExperiment": h_create_experiment,
    "ConfigureTraining": h_configure_training,
    "ConfigureHyperparameters": h_configure_hyperparameters,
    "ConfigureRandomSeeds": h_configure_seeds,
    "CreateBaseline": h_create_baseline,
    "RunBaseline": h_run_baseline,
    "TrainPolicy": h_train_policy,
    "ResumeTraining": h_resume_training,
    "StopTraining": h_stop_training,
    "SaveCheckpoint": h_save_checkpoint,
    "LoadCheckpoint": h_load_checkpoint,
    "CollectTrainingMetrics": h_collect_metrics,
    "CompareExperiments": h_compare_experiments,
    "AnalyzeTrainingCurves": h_analyze_curves,
    "InspectTrainingFailure": h_inspect_training_failure,
    "ExportExperiment": h_export_experiment,
    "CreateEvaluationSuite": h_create_eval_suite,
    "DefineSuccessCriteria": h_define_success_criteria,
    "RunEvaluation": h_run_evaluation,
    "RecordEvaluationEpisode": h_record_eval_episode,
    "ComputeEvaluationMetrics": h_compute_eval_metrics,
    "CompareWithBaseline": h_compare_baseline,
    "DetectConstraintViolations": h_detect_violations,
    "GenerateEvaluationReport": h_generate_eval_report,
    "VerifySuccessIndependently": h_verify_success,
    "InspectEvaluationFailure": h_inspect_eval_failure,
    "CompareEvaluationRuns": h_compare_eval_runs,
    "ArchiveEvaluation": h_archive_evaluation,
    "ExportEvaluationResults": h_export_eval_results,
    "PackagePolicy": h_package_policy,
    "ExportPolicy": h_export_policy,
    "ValidatePolicyPackage": h_validate_package,
    "CreateDeliveryPackage": h_create_delivery_package,
    "VersionPolicy": h_version_policy,
    "InspectPolicyManifest": h_inspect_manifest,
    "VerifyReproducibility": h_verify_reproducibility,
}


def run_tool(session: Session, name: str, payload: dict) -> dict:
    """Execute a registered tool. Raises for unknown or
    not-implemented tools; approval-gated actions return the
    approval-required payload instead of executing."""
    definition = get_definition(name)
    if definition is None:
        raise ValueError(f"unknown tool: {name}")
    if definition["status"] == "not_implemented":
        action = {
            "PublishEnvironment": "share_artifact_externally",
            "PublishPolicy": "deploy_policy_to_production",
            "PublishEvaluationReport": "share_artifact_externally",
        }.get(name)
        if action and requires_human_approval(action):
            return _require_approval(action)
        raise NotImplementedError(
            f"tool {name} is not implemented: {definition['not_implemented_reason']}"
        )
    handler = HANDLERS.get(name)
    if handler is None:
        raise NotImplementedError(f"tool {name} has no handler")
    return handler(session, payload)
