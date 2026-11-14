# CartPole slice — measured results

Run: 20261114-173100 (SQLite local, worker CLI, no mocks)

## Baseline (random policy, 20 episodes)

- mean reward: 23.35
- median reward: 18.00
- mean length: 23.35

## Training (PPO, 20000 steps, seed 42)

- wall time: 59.5s
- final mean episode reward: 134.44
- best mean episode reward: 134.44

## Evaluation (20 episodes, deterministic, seed 100)

- mean reward: 498.70
- median reward: 500.00
- mean length: 498.70
- success rate (500-step episodes): 0.95 (19/20)

## Export

- package: local://packages/eba1109c-c2cf-4b31-97d4-cf6b6c6e2bcc/policy-package.zip
- independent validation (5 episodes, seed 1000): valid=True, mean reward 492.80, success rate 0.80
