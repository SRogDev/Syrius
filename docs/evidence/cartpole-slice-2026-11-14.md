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

## Re-run (Phase 7, 20261114-180527, same command)

- baseline mean reward: 20.30 (median 19.50, mean length 20.30)
- training wall time: 55.8s; final mean episode reward: 134.44
- evaluation: mean 498.70, median 500.00, success 0.95 (19/20)
- export validation: valid=True, mean 492.80, success 0.80

Note on the baseline: the random-policy mean is **not stable
across processes** with the same seed 0 — runs on 2026-11-14
measured 23.35, 22.30, 21.90, 20.85, 20.30 and 16.95 (clean-clone run).
The PPO training and evaluation numbers, by contrast, are
identical in every run (134.44 / 498.70). The baseline is reported
as measured each run, never as a fixed constant; the Phase 7 E2E
test asserts it only as `< 100`.
