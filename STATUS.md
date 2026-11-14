# STATUS.md — Syrius timeline

## Done

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

- Nothing active. Phase 0 is complete except the Blocked items below.

## Blocked (environment, not code)

- **PostgreSQL live check:** no Docker daemon in the build sandbox
  (`dockerd` fails: iptables permission denied even under sudo).
  `docker compose up`, `make migrate`, and the Docker image builds are
  unverified. `docker compose config` validates cleanly.
- **CI first run:** unobserved until the first push to GitHub Actions.

## Next

- **Phase 1 — First vertical slice** (per plan): one project, one
  environment (CartPole-v1), one real training run end to end.
  Requires: Gymnasium + Stable-Baselines3 install, projects/runs data
  model, OpenAPI-generated API client types (`packages/` appears then).
