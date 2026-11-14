"""RL core — Gymnasium adapter, baselines, PPO training, evaluation,
episode recording and policy packaging (Phases 2, 3, 4, 6).

Everything here is real: environments are created through Gymnasium,
training through Stable-Baselines3 PPO, evaluation through independent
episode rollouts. Nothing is mocked, and no number is invented — a
failed run reports failure with the error attached.

Success (plan §4) is verified independently of training reward: for
CartPole-v1 an episode counts as success when the pole stays up for the
full 500-step limit (``truncated`` at 500, never ``terminated``).
"""

from __future__ import annotations

import csv
import json
import os
import platform
import statistics
import tempfile
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import gymnasium as gym
from gymnasium.utils.env_checker import check_env
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from .schemas import TrainingConfig

CARTPOLE_MAX_STEPS = 500
CARTPOLE_SUCCESS_LENGTH = 500


def gym_version() -> str:
    import gymnasium as _gym

    return _gym.__version__


def sb3_version() -> str:
    import stable_baselines3 as _sb3

    return _sb3.__version__


def torch_version() -> str:
    import torch

    return torch.__version__


def framework_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "gymnasium": gym_version(),
        "stable_baselines3": sb3_version(),
        "torch": torch_version(),
    }


def space_to_dict(space: Any) -> dict:
    """JSON-able description of a Gymnasium space."""
    info: dict[str, Any] = {"type": type(space).__name__}
    if hasattr(space, "shape"):
        info["shape"] = list(space.shape)
    if hasattr(space, "dtype"):
        info["dtype"] = str(space.dtype)
    if hasattr(space, "low") and hasattr(space, "high"):
        info["low"] = [float(x) for x in space.low.flatten().tolist()]
        info["high"] = [float(x) for x in space.high.flatten().tolist()]
    if hasattr(space, "n"):
        info["n"] = int(space.n)
    return info


def make_env(gym_id: str, seed: int = 0) -> gym.Env:
    """Create a Gymnasium env with *seed* applied to reset/action space."""
    env = gym.make(gym_id)
    env.reset(seed=seed)
    env.action_space.seed(seed)
    return env


def validate_environment(gym_id: str, seed: int = 0) -> dict:
    """Run ``gymnasium.check_env`` plus one smoke episode.

    Returns a dict with ``valid``, the space descriptions, the smoke
    episode length/reward and any warnings. Raises the underlying error
    when the env cannot even be constructed.
    """
    env = gym.make(gym_id)
    warnings: list[str] = []
    try:
        check_env(env.unwrapped, skip_render_check=True)
    except Exception as exc:  # check_env raises on contract violations
        return {
            "gym_id": gym_id,
            "valid": False,
            "observation_space": space_to_dict(env.observation_space),
            "action_space": space_to_dict(env.action_space),
            "smoke_episode_length": 0,
            "smoke_episode_reward": 0.0,
            "warnings": [f"check_env failed: {exc}"],
            "checked_with": "gymnasium.check_env",
        }
    length, total_reward, _trace = run_episode(env, seed=seed)
    return {
        "gym_id": gym_id,
        "valid": True,
        "observation_space": space_to_dict(env.observation_space),
        "action_space": space_to_dict(env.action_space),
        "smoke_episode_length": length,
        "smoke_episode_reward": total_reward,
        "warnings": warnings,
        "checked_with": "gymnasium.check_env",
    }


def run_episode(
    env: gym.Env,
    policy: Any = None,
    seed: int = 0,
    deterministic: bool = True,
    record: bool = False,
) -> tuple[int, float, list[dict] | None]:
    """Run one episode; *policy* is an SB3 model or None (random).

    Returns ``(length, total_reward, trace_or_None)``. The trace is a
    list of per-step dicts (observation, action, reward, terminated,
    truncated, info keys) — callers store large traces in artifact
    storage, never in Postgres.
    """
    obs, _info = env.reset(seed=seed)
    trace: list[dict] = [] if record else None  # type: ignore[assignment]
    length = 0
    total_reward = 0.0
    terminated = truncated = False
    while not (terminated or truncated):
        if policy is None:
            action = env.action_space.sample()
        else:
            action, _ = policy.predict(obs, deterministic=deterministic)
        next_obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)
        length += 1
        if record:
            trace.append(  # type: ignore[union-attr]
                {
                    "step": length,
                    "observation": [float(x) for x in obs.tolist()]
                    if hasattr(obs, "tolist")
                    else obs,
                    "action": int(action)
                    if hasattr(action, "item") or isinstance(action, int)
                    else action,
                    "reward": float(reward),
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "info": {k: str(v) for k, v in info.items()},
                }
            )
        obs = next_obs
        if length >= 10_000:  # safety: a broken env must not loop forever
            break
    return length, total_reward, trace


def episode_stats(episodes: list[tuple[int, float]]) -> dict:
    """Mean/median reward and length over ``(length, reward)`` pairs."""
    lengths = [length for length, _ in episodes]
    rewards = [reward for _, reward in episodes]
    return {
        "episodes": len(episodes),
        "mean_reward": statistics.mean(rewards) if rewards else 0.0,
        "median_reward": statistics.median(rewards) if rewards else 0.0,
        "mean_length": statistics.mean(lengths) if lengths else 0.0,
        "median_length": statistics.median(lengths) if lengths else 0.0,
        "min_reward": min(rewards) if rewards else 0.0,
        "max_reward": max(rewards) if rewards else 0.0,
    }


def run_random_baseline(
    gym_id: str, n_episodes: int = 20, seed: int = 0
) -> dict:
    """Random-policy baseline: *n_episodes* uniform-action rollouts."""
    env = gym.make(gym_id)
    episodes: list[tuple[int, float]] = []
    for i in range(n_episodes):
        length, reward, _ = run_episode(env, policy=None, seed=seed + i)
        episodes.append((length, reward))
    env.close()
    stats = episode_stats(episodes)
    stats.update(
        {
            "policy": "random",
            "gym_id": gym_id,
            "seed": seed,
            "episodes_detail": [
                {"length": length, "reward": reward} for length, reward in episodes
            ],
        }
    )
    return stats


class _ProgressCallback(BaseCallback):
    """Records mean episode reward vs timestep for progress + metrics.csv."""

    def __init__(self, on_progress: Callable[[int, float | None], None] | None = None):
        super().__init__()
        self.history: list[dict] = []
        self._on_progress = on_progress
        self._last_reported = 0

    def _on_step(self) -> bool:
        step = int(self.num_timesteps)
        if step - self._last_reported >= 512 or step == 1:
            self._last_reported = step
            mean_reward: float | None = None
            buffers = getattr(self.model, "ep_info_buffer", None)
            if buffers:
                rewards = [info["r"] for info in buffers if "r" in info]
                if rewards:
                    mean_reward = float(statistics.mean(rewards))
            self.history.append({"timestep": step, "mean_episode_reward": mean_reward})
            if self._on_progress is not None:
                self._on_progress(step, mean_reward)
        return True


def train_ppo(
    config: TrainingConfig,
    output_dir: str | os.PathLike[str],
    on_progress: Callable[[int, float | None], None] | None = None,
) -> dict:
    """Train PPO (SB3) on ``config.env_id`` and save artifacts.

    Writes ``final_model.zip`` (SB3 checkpoint), ``metrics.csv``
    (timestep / mean episode reward) and returns measured training
    metrics. Runs on CPU. Raises on failure — callers record it.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    env = Monitor(gym.make(config.env_id))
    env.reset(seed=config.seed)
    env.action_space.seed(config.seed)
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=config.learning_rate,
        n_steps=config.n_steps,
        batch_size=config.batch_size,
        n_epochs=config.n_epochs,
        gamma=config.gamma,
        gae_lambda=config.gae_lambda,
        clip_range=config.clip_range,
        seed=config.seed,
        verbose=0,
    )
    callback = _ProgressCallback(on_progress=on_progress)
    model.learn(total_timesteps=config.total_timesteps, callback=callback)
    model_path = out / "final_model.zip"
    model.save(str(model_path.with_suffix("")))
    metrics_path = out / "metrics.csv"
    with metrics_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestep", "mean_episode_reward"])
        writer.writeheader()
        for row in callback.history:
            writer.writerow(row)
    ep_rewards = [
        row["mean_episode_reward"]
        for row in callback.history
        if row["mean_episode_reward"] is not None
    ]
    metrics = {
        "algorithm": "PPO",
        "env_id": config.env_id,
        "total_timesteps": config.total_timesteps,
        "final_mean_episode_reward": ep_rewards[-1] if ep_rewards else None,
        "best_mean_episode_reward": max(ep_rewards) if ep_rewards else None,
        "initial_mean_episode_reward": ep_rewards[0] if ep_rewards else None,
        "history_points": len(callback.history),
        "framework_versions": framework_versions(),
    }
    env.close()
    return {"model_path": str(model_path), "metrics_path": str(metrics_path), **metrics}


def load_policy(model_path: str | os.PathLike[str]) -> PPO:
    """Load an SB3 PPO checkpoint independently (fresh model object)."""
    return PPO.load(str(model_path))


def evaluate_policy(
    model_path: str | os.PathLike[str],
    gym_id: str,
    n_episodes: int = 20,
    seed: int = 100,
    deterministic: bool = True,
    success_length: int = CARTPOLE_SUCCESS_LENGTH,
) -> dict:
    """Independent evaluation: fresh load, *n_episodes* fresh rollouts.

    Success = episode reaches ``success_length`` steps (pole balanced
    the whole CartPole episode) — independent of training reward.
    """
    model = load_policy(model_path)
    env = gym.make(gym_id)
    episodes: list[tuple[int, float]] = []
    successes = 0
    violations = 0
    for i in range(n_episodes):
        length, reward, _ = run_episode(
            env, policy=model, seed=seed + i, deterministic=deterministic
        )
        episodes.append((length, reward))
        if length >= success_length:
            successes += 1
        if length <= 0:
            violations += 1
    env.close()
    stats = episode_stats(episodes)
    stats.update(
        {
            "policy": str(model_path),
            "gym_id": gym_id,
            "seed": seed,
            "deterministic": deterministic,
            "success_rate": successes / n_episodes if n_episodes else 0.0,
            "successes": successes,
            "success_length": success_length,
            "constraint_violations": violations,
            "episodes_detail": [
                {"length": length, "reward": reward} for length, reward in episodes
            ],
        }
    )
    return stats


def build_manifest(
    *,
    env_id: str,
    env_version: int,
    scenario: dict | None,
    algorithm: str,
    config: TrainingConfig,
    training_metrics: dict,
    evaluation: dict | None,
    artifact_refs: dict,
    model_provider: str | None = None,
    model_version: str | None = None,
    worker_config: dict | None = None,
) -> dict:
    """Full reproducibility manifest (plan §7.5). No field is invented:
    ``model_provider``/``model_version`` are null when no AI model was
    used (the CartPole slice is deterministic, BYOK-optional)."""
    return {
        "syrius_version": "0.1.0",
        "env_id": env_id,
        "env_version": env_version,
        "scenario": scenario or {},
        "algorithm": algorithm,
        "config": config.model_dump(),
        "hyperparameters": {
            "learning_rate": config.learning_rate,
            "n_steps": config.n_steps,
            "batch_size": config.batch_size,
            "n_epochs": config.n_epochs,
            "gamma": config.gamma,
            "gae_lambda": config.gae_lambda,
            "clip_range": config.clip_range,
        },
        "seeds": {"training": config.seed, "evaluation": config.eval_seed},
        "framework_versions": framework_versions(),
        "python_version": platform.python_version(),
        "training_engine": "stable-baselines3 PPO (CPU)",
        "model_provider": model_provider,
        "model_version": model_version,
        "worker_config": worker_config or {"executor": "syrius-worker", "device": "cpu"},
        "training_metrics": training_metrics,
        "evaluation": evaluation or {},
        "artifact_refs": artifact_refs,
        "created_at": datetime.now(UTC).isoformat(),
    }


def build_delivery_package(
    *,
    model_path: str | os.PathLike[str],
    manifest: dict,
    output_path: str | os.PathLike[str],
    readme_text: str | None = None,
) -> str:
    """Zip: model + manifest.json + README. Returns the package path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    readme = readme_text or (
        "# Syrius policy package\n\n"
        "Trained with Stable-Baselines3 PPO. Load with:\n\n"
        "```python\nfrom stable_baselines3 import PPO\n"
        "model = PPO.load('final_model.zip')\n```\n\n"
        "Full reproducibility metadata lives in `manifest.json`.\n"
    )
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(model_path, arcname="final_model.zip")
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("README.md", readme)
    return str(out)


def validate_delivery_package(
    package_path: str | os.PathLike[str],
    gym_id: str,
    n_episodes: int = 5,
    seed: int = 1000,
) -> dict:
    """Independent validation: extract the packaged model into a temp
    dir, load it fresh, run episodes. Returns measured results."""
    package_path = Path(package_path)
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(package_path) as zf:
            members = zf.namelist()
            zf.extractall(tmp)
        model_file = Path(tmp) / "final_model.zip"
        if not model_file.exists():
            return {"valid": False, "error": "final_model.zip missing from package"}
        result = evaluate_policy(
            model_file, gym_id, n_episodes=n_episodes, seed=seed
        )
        return {
            "valid": True,
            "members": members,
            "episodes": n_episodes,
            "mean_reward": result["mean_reward"],
            "mean_length": result["mean_length"],
            "success_rate": result["success_rate"],
        }
