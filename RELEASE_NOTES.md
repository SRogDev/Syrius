# Syrius v0.1.0 — Release notes

RL Engineering Factory: departments, studios and reproducible
reinforcement-learning pipelines. MIT — © 2026 Roger Modesto Oria
González.

## What v0.1 is

The complete Phases 0–7 scope: monorepo (pnpm + uv workspaces),
FastAPI backend with the full `/api/v1/` surface (42 paths), a
Postgres-backed job queue with a real worker loop, LangGraph
training workflows, SB3 PPO training on Gymnasium CartPole-v1, an
independent evaluation suite, policy packaging/export with a
reproducibility manifest, the Four Studios (Project, Environment,
Experiment, Evaluation + Deliverables), and the Phase 7 hardening
pass (E2E acceptance, list/history/download endpoints, security
review, dependency audit).

## Measured results (2026-11-14, this VM, no mocks)

Phase 7 end-to-end acceptance (`make e2e`, run 20261114-182115,
SQLite + real worker CLI, exit 0, 79.5 s wall):

- Baseline (random policy, 20 episodes): mean reward **21.90**
- Training (PPO, 20,000 steps, seed 42): **54.3 s**, final mean
  episode reward 134.44; training history 40 points
- Evaluation (20 episodes, deterministic, seed 100): mean **498.70**,
  median 500.00, success rate **0.95** (19/20)
- Export: package downloaded via `GET /artifacts/{id}/download`
  (115,041 bytes, sha256 verified); independent validation (5
  episodes, seed 1000): valid, mean **492.80**, success 0.80

Fresh slice re-run (`make slice`, 20261114-180527): baseline 20.30,
training 55.8 s / 134.44, evaluation 498.70 / 0.95, export 492.80 /
0.80. The random baseline mean varies run to run with the same seed
(16.95–23.35 across six runs); PPO training and evaluation are
identical every run.

## Verification (2026-11-14)

- `make check`: ruff clean, Biome clean (68 files), api pytest
  **37/37**, worker pytest **4/4**, web production build green
- `pnpm --filter syrius-web test`: Vitest **30/30**; typecheck clean
- `pnpm --filter syrius-docs build`: 7 pages
- First-run guide verified step by step on a clean clone
- Security review: no committed secrets; storage-path traversal
  guard added and tested; no stack-trace leakage in error responses
- `pip-audit`: 11 known vulnerabilities, all LangGraph family
  (fix = LangGraph 1.x upgrade — not in v0.1, recorded as future
  work; the reported attack prerequisites do not apply to the v0.1
  shape — in-memory MemorySaver checkpointer only, no
  langgraph-sdk auth decorators)

## What is NOT in v0.1

Auth, paid compute, production deploys, training resume, job
logs/resource-usage, scenario comparison, a department/tasks model.
No live PostgreSQL/Docker verification (no Docker daemon in the
build sandbox) and no real-browser Studio run. The GitHub Actions
run for the release commit must be observed separately — CI status
at release time is recorded in `STATUS.md`, not claimed here.

## Install

```sh
git clone https://github.com/SRogDev/Syrius.git
cd Syrius
make install
cp .env.example .env
make slice   # SQLite path, no Docker needed
```

Full install, backup/restore and release steps:
`docs/src/content/docs/getting-started.md` and
`docs/src/content/docs/operations.md`.
