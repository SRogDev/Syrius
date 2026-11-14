# STATUS.md — Syrius timeline

## Done

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
- Tests: API 28/28, worker 6/6 (incl. Phase 0 tests fixed for CI);
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

- Nothing active. Phases 1–6 (backend) are complete except the Blocked
  items below. Phase 5 (Four Studios, frontend) is a separate builder.

## Blocked (environment, not code)

- **PostgreSQL live check:** no Docker daemon in the build sandbox
  (`dockerd` fails: iptables permission denied even under sudo).
  `docker compose up`, `make migrate`, and the Docker image builds are
  unverified. `docker compose config` validates cleanly. The same
  schema is exercised locally via `create_all` on SQLite.
- **CI first runs:** observed failing on 73fb96d (2026-11-14) — the
  Phase 0 worker tests assumed no database exists (CI runs a Postgres
  service) and Biome failed on the new generated types + docs files.
  Both fixed locally; re-observation on the next push is pending.

## Next

- **Phase 5 — Four Studios** (separate builder): the web frontend
  against `/api/v1/` + `packages/api-client/` types.
- **Phase 7 — Hardening:** per plan §18.
