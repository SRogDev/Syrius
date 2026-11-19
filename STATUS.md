# STATUS.md — Syrius timeline

## Done

### 2026-11-19 — Architectural evolution toward Polygrow's intelligence infrastructure (docs only, no code)

- Cross-system audit of Polygrow, Syrius, and Rustenwer against Roger's
  2026-11-19 directive: `docs/architecture/cross-system-report.md`
  (existing capabilities, duplicated infrastructure, capabilities worth
  preserving, missing capabilities, integration points, target
  architecture, backward-compat risks, migration sequence R0–R4/S0–S4,
  files that should change, features that must remain untouched) +
  `docs/architecture/polygrow-and-rustenwer-integration.md` (§5.2
  integration doc) + ownership-boundary section in the Starlight
  Architecture page (`docs/src/content/docs/architecture.md`).
- Key decisions recorded: Polygrow owns shared intelligence/compute
  infrastructure; **Modal is the only initial remote compute provider**
  (no remote-provider code exists in this repo); Rustenwer is the
  complementary model-engineering system, collaboration via explicit
  contracts, no cross-repo imports. Phases S1–S4 are open work, gated on
  Roger's decisions (Modal account, auth/tenancy).
- Evidence at audit: API 37/37, worker 4/4, web Vitest 30/30, `ruff`
  clean.
- The API route count is **44 paths under `/api/v1/`** (43 `@router`
  decorators + the v1 health endpoint) — the README's "42 paths" is
  corrected in the same change.

### 2026-11-14 — Phase 7: Hardening (v0.1)

- **E2E acceptance** (`scripts/e2e_cartpole.py`, `make e2e`): real API
  - real worker, fresh SQLite, no mocks. Measured: baseline mean
    21.90; PPO 20,000 steps in 54.3 s; evaluation mean 498.70/500,
    success 0.95 (19/20); export download sha256-verified (115,041
    bytes); independent validation mean 492.80, success 0.80. Exit 0,
    total wall 79.5 s. Evidence in
    `docs/evidence/e2e-cartpole-2026-11-14.md`.
- **Gap endpoints (small, tested):** `GET /experiments`,
  `/evaluations`, `/episodes` (parent-id filters);
  `GET /experiments/{id}/history` (persisted metrics.csv rows, 40
  points, last timestep 19969); `GET /artifacts/{id}/download`
  (bytes, 501 for non-local, 400 for escaping `local://` URIs).
  9 new API tests.
- **Security fix:** `resolve_local_path` now refuses URIs escaping
  the storage root (was a real traversal hole for crafted artifact
  rows). Security review: no committed secrets, `.env` gitignored,
  `.env.example` placeholders only, no arbitrary shell/Python
  execution anywhere in api/worker code, no credential in prompts/
  logs/artifacts, no stack-trace leakage (verified live: 404/501
  bodies carry only `detail`).
- **Dependency audit:** `pip-audit` on the API env — 11 known
  vulnerabilities, all LangGraph family (langgraph 0.6.8,
  langgraph-checkpoint 2.1.2, langgraph-sdk 0.2.15; fix = LangGraph
  1.x). Not upgraded in Phase 7: major-version bump, own
  verification needed; Syrius uses only the in-memory MemorySaver
  checkpointer and no langgraph-sdk auth decorators, so the reported
  prerequisites do not apply to the v0.1 shape. `pnpm audit` could
  not run in the sandbox (registry request timed out);
  `npm audit` fails with ENOLOCK (pnpm workspace, no npm lockfile).
- **Studios wired to the new endpoints:** Experiment chart plots
  persisted history + live SSE points; Deliverables tab downloads
  the package zip; api.ts has list/history/download clients
  (Vitest 30/30); api-client types regenerated (42 paths).
- **Docs:** first-run guide verified step by step on a clean clone
  (install ✓, `make up`/`make migrate` ✗ no Docker daemon,
  dev-api health degraded/unavailable honest, `make slice` ✓,
  `make check` ✓); guide rewritten for the two paths;
  operations page (install/backup/restore/release) added;
  `RELEASE_NOTES.md` created.
- **Fresh slice re-run** (`make slice`, 20261114-180527): baseline
  20.30, training 55.8 s / 134.44, evaluation 498.70 / 0.95,
  export 492.80 / 0.80. Baseline mean varies run to run with the
  same seed (16.95–23.35 across six runs); PPO numbers are
  identical every run.
- Tests: API **37/37** (28 + 9 new), worker **4/4** — correcting the
  earlier "worker 6/6" line, which was wrong: the worker suite has
  always had 4 tests (2 status/heartbeat + 2 run-loop).
- `make check` (ruff, Biome, pytest api + worker, web build) green;
  `pnpm --filter syrius-web test` 30/30, typecheck clean, docs
  build 7 pages.

### 2026-11-14 — Phases 1, 2, 3, 4, 6: backend vertical slice (v0.1)

- Core domain: SQLAlchemy models + Alembic migration 0002 for all §12
  slice entities; EngineeringCapability contract; 71 tool definitions;
  audit/provenance events; local storage (real) + S3 interface.
- RL: Gymnasium adapter (CartPole-v1 validated via check_env), random
  baseline, SB3 PPO training, independent evaluation (success = full
  500-step episode), policy packaging/export with full manifest.
- Jobs: Postgres-backed queue (lease/heartbeat/retry/cancel, row
  locking) + worker `run` loop; LangGraph training workflow with
  persisted execution state; SSE live progress.
- API: full `/api/v1/` (38 paths) + OpenAPI-generated TS types in
  `packages/api-client/`.
- **Measured acceptance run** (`scripts/run_cartpole_slice.py`,
  SQLite local, real worker CLI): baseline mean 23.35; PPO 20,000
  steps in 59.5 s; evaluation mean 498.70/500, success 0.95 (19/20);
  export independently validated (mean 492.80, success 0.80).
  Evidence in `docs/evidence/cartpole-slice-2026-11-14.md`.
- Tests: API 28/28, worker 4/4 (corrected — see Phase 7 entry);
  ruff + Biome clean.
- CI: first runs observed failing on 73fb96d (worker tests assumed no
  DB; Biome on generated types/docs) — both fixed locally, pending
  re-observation on the next push.

### 2026-11-14 — Phase 0: Repository Foundation (v0.1)

- Monorepo skeleton: pnpm workspaces (web, docs) + uv workspace (api, worker).
- Web: TanStack Start 1.169.5 SPA (verified via official `@tanstack/cli`
  scaffold), React 19.3.1, Tailwind 4.3.5. Routes `/`, `/projects`,
  `/projects/$projectId`; home shows a live API health panel backed by
  React Query against the real API. Build + strict typecheck pass.
- API: FastAPI with `GET /health` and `GET /api/v1/health`, honest DB
  reachability flag. pytest 3/3 (RED→GREEN).
- Worker: `status` / `heartbeat` CLI with DB-backed registration row.
  pytest 2/2 (RED→GREEN).
- PostgreSQL 16 via Docker Compose (named volume, healthcheck) + Alembic
  baseline migration `0001` (`worker_registrations` table).
- Docs: Astro Starlight (6 pages incl. Getting started, Architecture,
  Versions, Development). Build passes.
- CI: GitHub Actions (Python ruff+pytest with a Postgres service, web
  build+typecheck+Biome, docs build).
- Toolchain versions verified against live registries and recorded in
  `docs/architecture/versions.md`.

## Doing

- Nothing active. Phases 0–7 are complete except the Blocked items
  below.

## Blocked (environment, not code)

- **PostgreSQL live check:** no Docker daemon in the build sandbox
  (`dockerd` fails: iptables permission denied even under sudo).
  `docker compose up`, `make migrate`, and the Docker image builds are
  unverified. `docker compose config` validates cleanly. The same
  schema is exercised locally via `create_all` on SQLite.
- **CI:** observed GREEN on the Phase 7 final push — Actions run
  43626409634 for `4261a02`: python, web and docs jobs all
  `completed / success`. The 73fb96d failures are fixed and verified
  on `main`.
- **Dependency audit (JS):** `pnpm audit` cannot reach the npm
  registry audit endpoint from this sandbox (request timed out);
  `npm audit` needs an npm lockfile the pnpm workspace does not
  have. No JS audit result exists for v0.1.
- **LangGraph 1.x upgrade:** `pip-audit` finds 11 vulnerabilities
  in langgraph 0.6.8 / langgraph-checkpoint 2.1.2 / langgraph-sdk
  0.2.15 (fix: 1.0.10 / 3.0.0–4.1.1 / 0.3.15–0.4.4). Major-version
  upgrade, needs its own verification pass — future work, not done
  in Phase 7.

## Next

- **After v0.1 (future work, explicitly out of Phase 7 scope):**
  training resume, job logs/resource-usage endpoint,
  scenario-comparison endpoint, department/tasks model, episode and
  evaluation pickers wired to the Phase 7 list endpoints, LangGraph
  1.x upgrade, live PostgreSQL/Docker verification, real-browser run
  of the Studios (responsive breakpoints, canvas playback, ECharts
  rendering).
