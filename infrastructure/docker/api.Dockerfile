# Syrius API image (Phase 0).
# Not verified by a live `docker build` in this sandbox (no Docker daemon);
# see IMPLEMENTATION_STATUS.md.
FROM ghcr.io/astral-sh/uv:0.12.19-python3.12-bookworm-slim
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "syrius_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
