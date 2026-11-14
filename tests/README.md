# tests/

Reserved for future cross-app end-to-end tests (Phase 1+).

In Phase 0, tests live next to the code they cover:

- `apps/api/tests/` — API health endpoint tests (pytest)
- `apps/worker/tests/` — worker status/heartbeat tests (pytest)

This directory stays intentionally almost empty until the first real
end-to-end test exists. Do not add placeholder test files here.

The first real end-to-end test lives in `scripts/e2e_cartpole.py`
(Phase 7): the full CartPole slice through the real API + real
worker, run with `make e2e`. `scripts/run_cartpole_slice.py`
(`make slice`) is the original acceptance run.
