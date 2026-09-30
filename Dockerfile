# ==============================
# Builder
# ==============================

FROM python:3.11-slim-trixie AS builder


# Pin uv version for reproducibility.
# 使用南京大学 ghcr 镜像（大陆直连 ghcr.io 会被墙）。
COPY --from=ghcr.nju.edu.cn/astral-sh/uv:0.12.19 \
    /uv /uvx /bin/


ENV UV_PYTHON_DOWNLOADS=0
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1


WORKDIR /app


# Dependency layer.
COPY pyproject.toml uv.lock ./


RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --locked \
    --no-dev \
    --no-install-project


# ==============================
# Runtime
# ==============================

FROM python:3.11-slim-trixie AS runtime


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"


WORKDIR /app


# Create non-root user.
RUN groupadd \
        --gid 10001 \
        app \
    && useradd \
        --uid 10001 \
        --gid 10001 \
        --create-home \
        app


COPY --from=builder \
    --chown=app:app \
    /app/.venv \
    /app/.venv


COPY --chown=app:app \
    src \
    /app/src


USER app


EXPOSE 8000


HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=20s \
    --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" \
    || exit 1


CMD ["uvicorn", "ecom_agent_os.api.app_async:app", "--host", "0.0.0.0", "--port", "8000"]