# Syrius worker image (Phase 0).
# Not verified by a live `docker build` in this sandbox (no Docker daemon);
# see IMPLEMENTATION_STATUS.md.
FROM ghcr.io/astral-sh/uv:0.12.19-python3.12-bookworm-slim
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
RUN uv sync --frozen --no-dev

# Phase 0: one heartbeat, then exit. The long-running loop is Phase 1.
CMD ["uv", "run", "--no-sync", "python", "-m", "syrius_worker.main", "heartbeat"]
