// Dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PRIORITY=strict \
    UV_VERSION=0.1.18

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for faster package management
RUN pip install uv

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy dependency files
COPY --chown=appuser:appgroup pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache --compile \
    fastapi>=0.110.0 \
    uvicorn[standard]>=0.29.0 \
    sqlalchemy[asyncio]>=2.0.30 \
    asyncpg>=0.29.0 \
    alembic>=1.13.0 \
    pydantic>=2.6.0 \
    pydantic-settings>=2.2.0 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    python-multipart>=0.0.9 \
    email-validator>=2.1.0 \
    greenlet>=3.0.0

# Copy application code
COPY --chown=appuser:appgroup . /app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
