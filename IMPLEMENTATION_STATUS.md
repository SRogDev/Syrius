# IMPLEMENTATION_STATUS.md — Syrius v0.1

Honest tracking of Phase 0 requirements. States: **Not started** /
**In progress** / **Implemented** / **Tested** / **Blocked**.

Evidence for every Tested item is in the "Evidence" column (command +
result, all run on the build VM on 2026-11-14). Blocked items name the
exact failure — nothing is faked green.

## Phase 0 — Repository Foundation

| #    | Requirement                                                                                                     | State       | Evidence / note                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---- | --------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1  | Monorepo skeleton (pnpm workspaces + uv workspace)                                                              | Tested      | `pnpm install` — 368 packages; `uv sync` — workspace resolves, both packages build with `uv_build`                                                                                                                                                                                                                                                                                                                                           |
| 0.2  | Web: TanStack Start SPA skeleton that loads (routing shell + home/project pages, real API health, no mock data) | Tested      | `pnpm --filter syrius-web build` — SPA prerender of `/` OK; `vite preview` on :4173 — `/` 200, `/projects` 200, logo 200; shell contains live "Probing API" panel                                                                                                                                                                                                                                                                            |
| 0.3  | API: FastAPI `GET /health` + `GET /api/v1/health` with real DB reachability flag, CORS for local web            | Tested      | pytest 3/3; live `uvicorn` — both endpoints return `{"status":"degraded","db":"unavailable"}` with no DB (honest); unknown route 404                                                                                                                                                                                                                                                                                                         |
| 0.4  | Worker: registers itself, reports status (heartbeat/status CLI + DB-backed row, honest "db unavailable")        | Tested      | pytest 2/2; live CLI `status` prints `db: unavailable`, exit 1, with no DB                                                                                                                                                                                                                                                                                                                                                                   |
| 0.5  | PostgreSQL via docker-compose (postgres:16-alpine, named volume, healthcheck)                                   | Blocked     | `docker compose config -q` validates (exit 0). **Live run blocked:** no Docker daemon in sandbox — `dockerd` fails with `iptables ... Permission denied (you must be root) (exit status 4)` even under sudo                                                                                                                                                                                                                                  |
| 0.6  | Alembic initialized + initial baseline migration                                                                | Implemented | Migration `0001` creates `worker_registrations`. **Live apply Blocked** — needs Postgres (see 0.5); `make migrate` fails honestly on connection refused                                                                                                                                                                                                                                                                                      |
| 0.7  | `.env.example` (placeholders only, no secrets)                                                                  | Implemented | Reviewed — placeholders only                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 0.8  | Makefile (install, dev, test, lint, migrate, up/down)                                                           | Tested      | `make install`, `make test`, `make lint`, `make check` run. `make up` / `make migrate` Blocked by 0.5 (Docker)                                                                                                                                                                                                                                                                                                                               |
| 0.9  | Root files: README, LICENSE (MIT, SRogDev 2026), CONTRIBUTING, .gitignore, pnpm-workspace.yaml, pyproject.toml  | Implemented | All present; README states Phase 0 scope and what is NOT built                                                                                                                                                                                                                                                                                                                                                                               |
| 0.10 | CI: `.github/workflows/ci.yml` (ruff, Biome, pytest, web build, docs build)                                     | Implemented | Workflow written; first runs observed 2026-11-14 — failing on 73fb96d (worker tests assumed no DB; Biome on generated types/docs); both fixed locally, re-observation pending                                                                                                                                                                                                                                                                |
| 0.11 | Version verification before pinning + `docs/architecture/versions.md`                                           | Implemented | npm/PyPI checked 2026-11-14; TanStack Start SPA config verified via official `@tanstack/cli` scaffold + docs                                                                                                                                                                                                                                                                                                                                 |
| 0.12 | Tests with evidence (TDD RED→GREEN)                                                                             | Tested      | API: RED `ModuleNotFoundError: No module named 'syrius_api.main'` → GREEN 3 passed. Worker: RED `ModuleNotFoundError: No module named 'syrius_worker.main'` → GREEN 2 passed                                                                                                                                                                                                                                                                 |
| 0.13 | Lint: Ruff + Biome + strict TS, zero errors                                                                     | Tested      | `ruff check` — all checks passed; `biome check .` — 27 files, no errors; `tsc --noEmit` — exit 0                                                                                                                                                                                                                                                                                                                                             |
| 0.14 | Docs: Astro Starlight skeleton (getting-started, architecture, development) with real install steps             | Tested      | `pnpm --filter syrius-docs build` — 6 pages built (Phase 0); docs build re-verified after Phases 1–6 edits                                                                                                                                                                                                                                                                                                                                   |
| 0.15 | AGENTS.md + STATUS.md (repo-docs standard)                                                                      | Implemented | Both present at repo root                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 0.16 | Dockerfiles for API/worker                                                                                      | Implemented | Written; **live `docker build` Blocked** by 0.5 (no daemon)                                                                                                                                                                                                                                                                                                                                                                                  |
| 0.17 | GitHub push + remote == local verification                                                                      | Tested      | Pushed via SSH git (proxy tunnel, host ssh.github.com:443). Remote main `b44d130ad9f91d7e299268a258c296c86c94a8c2`, tree `cabcb3b029b24780ac73cff8674eacd8cc8169dc` — verified equal to local HEAD/tree via fresh fetch + `git ls-remote` 2026-11-14. Note: remote was NOT empty — it held Roger's `Initial commit` (LICENSE only, `3b4527e`); local work was rebased onto it and the LICENSE conflict resolved to Roger's full-name version |

## Phases 1–7 — correct plan phases (plan §18)

The Phase 0 table above was inaccurate shorthand. The real phases are:
0 Foundation, 1 Core Domain + Capability, 2 RL Architect + Environment
Factory, 3 Experiment Factory + Training, 4 Evaluation & QA,
5 Four Studios, 6 Deployment Factory, 7 Hardening.

| Phase | Scope (per plan §18)               | State                                                  |
| ----- | ---------------------------------- | ------------------------------------------------------ |
| 0     | Foundation                         | Tested (see above; Postgres/Docker live paths Blocked) |
| 1     | Core Domain + Capability           | Tested                                                 |
| 2     | RL Architect + Environment Factory | Tested                                                 |
| 3     | Experiment Factory + Training      | Tested                                                 |
| 4     | Evaluation & QA                    | Tested                                                 |
| 5     | Four Studios (frontend)            | Not started — separate builder                         |
| 6     | Deployment Factory                 | Tested                                                 |
| 7     | Hardening                          | Not started                                            |

## Phase 1 — Core Domain + Capability

| #   | Requirement                                                                                                                                            | State       | Evidence / note                                                                                                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1.1 | Project, Artifact, Environment, Experiment, Job models (SQLAlchemy + Alembic 0002)                                                                     | Tested      | `apps/api/tests/test_domain.py` + `test_api_slice.py`; migration 0002 creates all §12 slice tables                          |
| 1.2 | EngineeringCapability contract (§7.2) with input/output validation, permissions, resource limits, cancellation, retry, logging, provenance, versioning | Tested      | `test_domain.py::test_capability_validation_permissions_limits`; `capabilities.py`                                          |
| 1.3 | Tool registry (§7.3): definitions separate from execution; no arbitrary shell/Python execution                                                         | Tested      | `test_tools.py`; 71 definitions; handlers are fixed functions                                                               |
| 1.4 | Audit/provenance events                                                                                                                                | Tested      | `audit_events` table; `record_audit` on project create, training, baseline, evaluation, export                              |
| 1.5 | Storage abstraction: local filesystem real; S3 adapter interface + boto3 impl, fails loudly without boto3                                              | Tested      | `test_domain.py::test_local_storage_roundtrip_and_traversal_guard`, `test_s3_storage_without_boto3_or_bucket_raises`        |
| 1.6 | Human approval boundaries (§13) recorded in code/config; no paid-compute paths                                                                         | Implemented | `capabilities.py`: `REQUIRES_HUMAN_APPROVAL`, `PAID_COMPUTE_ACTIONS`; approval-gated tools return `requires_human_approval` |

## Phase 2 — RL Architect + Environment Factory

| #   | Requirement                                                                                          | State       | Evidence / note                                                                                 |
| --- | ---------------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| 2.1 | Gymnasium adapter; CartPole-v1 fully working built-in env                                            | Tested      | `test_rl.py::test_validate_cartpole` — check_env passes, Box[4] / Discrete(2)                   |
| 2.2 | Env validation (check_env + smoke episode), scenario metadata                                        | Tested      | `POST /api/v1/environments/validate` returns `valid: true`; Episode/Scenario models             |
| 2.3 | EpisodeTrace contract (§3.2): traces in artifact storage, NOT Postgres                               | Tested      | `test_tools.py::test_record_and_replay_episode`; `GET /episodes/{id}/trace`                     |
| 2.4 | RL problem specification model + 12 Architect tools (real definitions; deterministic where possible) | Tested      | `test_tools.py`; `POST /specifications/{id}/formalize` fills spaces/approach, gaps → `[]`       |
| 2.5 | 18 Environment Factory tools; CartPole-relevant ones real, others honest not-implemented             | Tested      | 16/18 implemented; `PublishEnvironment`, `DeprecateEnvironment` not-implemented with reasons    |
| 2.6 | AI-assisted generation BYOK-optional, never required for the CartPole slice                          | Implemented | No provider call exists in the slice path; BYOK `ProviderConnection` stores only a `secret_ref` |

## Phase 3 — Experiment Factory + Training

| #   | Requirement                                                                                                                          | State  | Evidence / note                                                                                                                        |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| 3.1 | Postgres-backed job queue (§8.2): states, retry count, lease/heartbeat, cancellation, logs, timestamps, worker identity; row locking | Tested | `test_domain.py::test_job_queue_claim_complete_retry_cancel`; `FOR UPDATE SKIP LOCKED` on Postgres, single-transaction claim on SQLite |
| 3.2 | Worker execution loop: claim, run, heartbeat, complete/fail, retry                                                                   | Tested | `apps/worker/tests/test_worker_run.py` 4/4; `syrius-worker run --once` drove the real slice                                            |
| 3.3 | PPO adapter + SB3 integration; random-policy baseline                                                                                | Tested | Acceptance run: baseline mean 23.35 (20 eps); PPO 20000 steps in 59.5 s                                                                |
| 3.4 | Training config per §10.2 exactly (editable + versioned)                                                                             | Tested | `schemas.TrainingConfig` defaults; acceptance run config asserted equal to §10.2                                                       |
| 3.5 | Live progress via SSE endpoint                                                                                                       | Tested | `test_api_slice.py::test_sse_progress_stream`; `GET /experiments/{id}/events`                                                          |
| 3.6 | Checkpoint save/load; metrics persistence (metrics.csv + DB rows)                                                                    | Tested | Checkpoint artifact + metrics.csv artifact in acceptance run; `GET /experiments/{id}/metrics`                                          |
| 3.7 | API never runs long training inside a request handler                                                                                | Tested | `test_train_is_enqueued_not_inline`: job stays `queued` after the request returns                                                      |
| 3.8 | LangGraph persistence for agent workflow state                                                                                       | Tested | `test_api_slice.py::test_workflow_run_creates_experiment_and_job`; StateGraph + MemorySaver + durable `workflow_executions` row        |
| 3.9 | 17 Experiment Factory tools as real definitions; CartPole-relevant ones working                                                      | Tested | 17/17 implemented                                                                                                                      |

## Phase 4 — Evaluation & QA

| #   | Requirement                                                                                                                              | State  | Evidence / note                                                                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| 4.1 | Evaluation suite model; independent success verifier (pole balanced / episode length, NOT training reward)                               | Tested | `EvaluationSuite`/`EvaluationRun`; success = 500-step episode                                      |
| 4.2 | Evaluation runner, episode recording, metrics (mean/median reward, mean length, success rate, failure conditions, constraint violations) | Tested | Acceptance run: mean 498.70, median 500.00, mean length 498.70, success 0.95 (19/20), violations 0 |
| 4.3 | Baseline comparison; reports report.json + report.md with measured numbers                                                               | Tested | `GET /evaluations/{id}/report`; `docs/evidence/cartpole-slice-2026-11-14.md`                       |
| 4.4 | 14 Evaluation tools as real definitions; CartPole path fully working                                                                     | Tested | 13/14 implemented; `PublishEvaluationReport` not-implemented (needs human approval, §13)           |

## Phase 6 — Deployment Factory

| #   | Requirement                                                                                          | State  | Evidence / note                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| 6.1 | Policy packaging + export: final_model.zip + manifest.json with full reproducibility metadata (§7.5) | Tested | Acceptance run export: manifest has env/algorithm/config/hyperparams/seeds/framework versions/training engine/worker config/timestamps |
| 6.2 | Inference interface metadata; delivery package (zip with model + manifest + README)                  | Tested | Package members: `final_model.zip`, `manifest.json`, `README.md`                                                                       |
| 6.3 | Validation of the artifact: independent load + episodes                                              | Tested | Export-time validation + independent re-validation in the acceptance script (5 eps, seed 1000: mean 492.8, success 0.80)               |
| 6.4 | 10 Deployment tools as definitions; packaging/export/validation working                              | Tested | 7/10 implemented; `PublishPolicy` (approval-gated), `RollbackPolicy`, `SignDeliveryPackage` not-implemented with reasons               |

## Phase 5 — Four Studios (frontend)

Not started. Separate builder. The backend exposes everything the
studios need via `/api/v1/` + OpenAPI-generated types in
`packages/api-client/src/types.ts` (38 paths).

## Phase 7 — Hardening

Not started.

## CartPole acceptance run (measured, 2026-11-14)

Real run: `scripts/run_cartpole_slice.py`, SQLite local, real worker
CLI, no mocks. Full numbers in
`docs/evidence/cartpole-slice-2026-11-14.md` (+ `.results.json`).

| Step                                              | Measured result                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------- |
| Baseline (random, 20 eps)                         | mean reward 23.35, median 18.00, mean length 23.35                        |
| Training (PPO, 20000 steps, seed 42)              | 59.5 s wall; final mean episode reward 134.44                             |
| Evaluation (20 eps, deterministic, seed 100)      | mean 498.70, median 500.00, mean length 498.70, success rate 0.95 (19/20) |
| Export validation (independent, 5 eps, seed 1000) | valid, mean 492.80, success rate 0.80                                     |

Note the honest gap: the training-loop mean (134.44, last-100-episode
rolling average during training) is far below the final policy's
evaluation (498.70) — the policy improved late in the run. The
20000-step budget is not claimed to "solve" CartPole; the measured
evaluation is what it is.

## Known limitations (Phases 0–6, by design or environment)

- **No live PostgreSQL verification anywhere.** API and worker health
  logic is tested with the DB down (honest `unavailable` path); the
  `db: ok` path is exercised only in CI (Postgres service) and has not
  been observed live yet. Migration 0002 applies to Postgres in CI;
  locally the same schema is exercised via `create_all` on SQLite.
- **CI first runs observed — failing on 73fb96d (2026-11-14).** Two
  jobs failed: (1) python — the Phase 0 worker tests assumed no
  database exists, but CI runs a Postgres service, so
  `test_status_reports_db_unavailable_without_postgres` saw `db: ok`
  (pre-existing Phase 0 failure, same step failed on 8216b35); fixed
  by forcing an unreachable `DATABASE_URL` in those tests.
  (2) web — `biome check` failed on the new generated
  `packages/api-client/src/types.ts` and the new docs files; fixed by
  making the generator emit Biome-style output and formatting the
  docs files. Re-verified locally (`biome check .` clean); CI must
  be re-observed on the next push.
- **Docker images unbuilt.** Dockerfiles are standard `uv`-based images
  but `docker build` was never executed here (no daemon in sandbox).
- **Web health panel verified via prerendered shell + preview only.**
  The client-side fetch (React Query against the live API) needs a
  browser run with both servers up; the code path is the standard
  `fetch('/api/v1/health')` through the Vite dev proxy.
- **Phase 5 (Four Studios) not built.** The web SPA still shows the
  Phase 0 shell; it does not surface projects, runs, or training yet.
- **`check_env` warnings are Gymnasium's own** (infinite Box bounds,
  wrapper notice) and appear in logs; validation still passes.
- **Torch is the CPU build (2.15.0+cpu)** — the PyTorch CPU index
  source only applies when torch is a direct dependency (verified);
  the CUDA build was replaced, no NVIDIA packages remain.
