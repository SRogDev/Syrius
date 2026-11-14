---

title: Operations
description: Install, back up, restore and release Syrius v0.1.
---

## Install

Prerequisites: Node.js 24 + pnpm 12, Python 3.12 + uv 0.12, Docker
only for PostgreSQL (see [Getting started](/getting-started/)).

```sh
git clone https://github.com/SRogDev/Syrius.git
cd Syrius
make install
cp .env.example .env
```

Verify with `make check` (ruff + Biome, pytest api 37 + worker 4,
web production build), `pnpm --filter syrius-web test` (Vitest 30)
and `make slice` (real CartPole run on SQLite, ~90 s).

## Backup and restore

There is no managed backup service in v0.1 — two things to copy:

1. **The database.** PostgreSQL: `pg_dump` against
   `DATABASE_URL` on a schedule set by the operator.

   ```sh
   pg_dump "$DATABASE_URL" > syrius-$(date +%Y%m%d).sql
   psql "$DATABASE_URL" < syrius-20261114.sql   # restore
   ```

   SQLite (local dev/tests): copy the database file while no
   worker is running — the file is the whole database.

2. **Artifact storage** (`STORAGE_DIR`, default `./var/storage`):
   checkpoints, metrics.csv files, episode traces, delivery
   packages. Back it up with the database — artifact rows in the
   DB point at these files by `storage_uri`, so a DB restore
   without the matching storage directory leaves dangling
   pointers. Restore both from the same point in time.

No backup/restore automation exists in v0.1; the operator owns the
schedule. Nothing in the repo deletes data except `docker compose
down -v` (which removes the named Postgres volume — use `down`
without `-v` to keep data).

## Release (v0.1)

1. `git log` on `main` must show the Phase 7 commits; the release
   notes live in `RELEASE_NOTES.md` at the repo root.
2. Verify: `make check`, `pnpm --filter syrius-web test`,
   `pnpm --filter syrius-web typecheck`,
   `pnpm --filter syrius-docs build`, `make slice`, `make e2e`.
   All must pass with the measured numbers recorded in
   `docs/evidence/` — never release on a stale run.
3. Tag the release from `main` (maintainer only, human pace):

   ```sh
   git tag -a v0.1.0 -m "Syrius v0.1.0 — CartPole vertical slice + Four Studios + hardening"
   git push origin v0.1.0
   ```

   No CI release job, no package publishing, and no production
   deploy exist in v0.1; the tag marks the verified commit only.
4. After tagging, confirm the GitHub Actions run for the release
   commit is green; if CI is unobserved, say so in the release
   notes instead of claiming it.

## Configuration reference

All runtime settings come from the environment (or `.env` at the
repo root) — see `.env.example`. Placeholders only; never commit a
real `.env` (it is gitignored). The only credentials in v0.1 are
the local Postgres user/password and the database URL.
