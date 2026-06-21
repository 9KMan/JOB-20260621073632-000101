# Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_USER=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for faster package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Python dependencies
FROM base as python-deps

COPY --link pyproject.toml .
# Install dependencies using uv for reproducibility
RUN uv sync --frozen --no-install-project

# Development image
FROM base as development

# Copy lockfile for dependency verification
COPY --link --from=python-deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}" \
    VIRTUAL_ENV=/app/.venv

# Copy source code
COPY --link src/ ./src/
COPY --link migrations/ ./migrations/
COPY --link alembic.ini .

# Create non-root user
RUN adduser --disabled-password --gecos '' apuser && chown -R apuser:apuser /app
USER apuser

EXPOSE 8000
CMD ["uvicorn", "src.core.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production image
FROM base as production

# Copy lockfile for dependency verification
COPY --link --from=python-deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}" \
    VIRTUAL_ENV=/app/.venv

# Copy source code
COPY --link src/ ./src/
COPY --link migrations/ ./migrations/
COPY --link alembic.ini .

# Non-root user for security
RUN addgroup --system --gid 1001 apgroup && \
    adduser --system --uid 1001 --gid 1001 --shell /bin/false --home /nonexistent apuser && \
    chown -R apuser:apgroup /app

USER apuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Run as module (production)
CMD ["uvicorn", "src.core.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
