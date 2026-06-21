# syntax=docker/dockerfile:1.6

# ----- Build stage -----
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels \
        "fastapi>=0.110" \
        "uvicorn[standard]>=0.29" \
        "sqlalchemy[asyncio]>=2.0.27" \
        "asyncpg>=0.29" \
        "alembic>=1.13" \
        "pydantic>=2.6" \
        "pydantic-settings>=2.2" \
        "python-jose[cryptography]>=3.3" \
        "passlib[bcrypt]>=1.7" \
        "python-multipart>=0.0.9" \
        "python-dotenv>=1.0" \
        "httpx>=0.27" \
        "tenacity>=8.2"

# ----- Runtime stage -----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home $APP_HOME app

WORKDIR $APP_HOME

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels \
    fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" \
    python-multipart python-dotenv httpx tenacity \
    && rm -rf /wheels

COPY --chown=app:app . $APP_HOME

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
