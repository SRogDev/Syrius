# E2E CartPole acceptance — measured results (Phase 7)

Run: 20261114-182115 (SQLite local, worker CLI, no mocks)

## Baseline (random policy, 20 episodes)

- mean reward: 21.90
- median reward: 20.00
- mean length: 21.90

## Training (PPO, 20000 steps, seed 42)

- wall time: 54.3s
- final mean episode reward: 134.44
- best mean episode reward: 134.44
- training-history points: 40 (last timestep 19969)

## Evaluation (20 episodes, deterministic, seed 100)

- mean reward: 498.70
- median reward: 500.00
- mean length: 498.70
- success rate (500-step episodes): 0.95 (19/20)

## Export

- package artifact: c447b35d-9e00-4284-8642-c886f3dcc403 (115041 bytes, downloaded via GET /artifacts/{id}/download, sha256 verified)
- independent validation (5 episodes, seed 1000): valid=True, mean reward 492.80, success rate 0.80

Total wall time: 79.5s
