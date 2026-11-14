# E2E CartPole acceptance — measured results (Phase 7)

Run: 20261114-180026 (SQLite local, worker CLI, no mocks)

## Baseline (random policy, 20 episodes)

- mean reward: 20.85
- median reward: 17.00
- mean length: 20.85

## Training (PPO, 20000 steps, seed 42)

- wall time: 54.2s
- final mean episode reward: 134.44
- best mean episode reward: 134.44
- training-history points: 40 (last timestep 19969)

## Evaluation (20 episodes, deterministic, seed 100)

- mean reward: 498.70
- median reward: 500.00
- mean length: 498.70
- success rate (500-step episodes): 0.95 (19/20)

## Export

- package artifact: 8d1613e3-211c-43f4-9249-07c3c7e174f4 (115035 bytes, downloaded via GET /artifacts/{id}/download, sha256 verified)
- independent validation (5 episodes, seed 1000): valid=True, mean reward 492.80, success rate 0.80

Total wall time: 83.8s
