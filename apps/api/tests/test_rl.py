"""Tests: RL core — env validation, random baseline, episode stats."""

from syrius_api import rl


def test_validate_cartpole() -> None:
    result = rl.validate_environment("CartPole-v1")
    assert result["valid"] is True
    assert result["gym_id"] == "CartPole-v1"
    assert result["observation_space"]["type"] == "Box"
    assert result["observation_space"]["shape"] == [4]
    assert result["action_space"]["type"] == "Discrete"
    assert result["action_space"]["n"] == 2
    assert result["smoke_episode_length"] > 0
    assert result["smoke_episode_reward"] == result["smoke_episode_length"]


def test_validate_unknown_env_raises() -> None:
    try:
        rl.validate_environment("NoSuchEnv-v9")
    except Exception:
        return
    raise AssertionError("unknown env id should raise")


def test_random_baseline_is_measured_not_invented() -> None:
    result = rl.run_random_baseline("CartPole-v1", n_episodes=5, seed=0)
    assert result["episodes"] == 5
    assert result["policy"] == "random"
    assert 0 < result["mean_length"] < 500
    assert len(result["episodes_detail"]) == 5
    assert result["mean_reward"] == result["mean_length"]  # CartPole: +1 per step


def test_episode_stats() -> None:
    stats = rl.episode_stats([(10, 10.0), (20, 20.0), (30, 30.0)])
    assert stats["mean_reward"] == 20.0
    assert stats["median_reward"] == 20.0
    assert stats["mean_length"] == 20.0
    assert stats["min_reward"] == 10.0
    assert stats["max_reward"] == 30.0


def test_framework_versions_reported() -> None:
    versions = rl.framework_versions()
    assert versions["gymnasium"] == "1.4.0"
    assert versions["stable_baselines3"] == "2.9.2"
    assert versions["python"].startswith("3.12")
    assert versions["torch"].startswith("2.15.0")
