# Dockerfile
# syntax=docker/dockerfile:1.7-labs

# ============================================
# Stage 1: Base
# ============================================
FROM python:3.11-slim-bookworm AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Create non-root user for running application
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# ============================================
# Stage 2: Development
# ============================================
FROM base AS development

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies including dev dependencies
RUN poetry install --all-extras --no-root

# Copy source code
COPY . .

# Change ownership of app directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command for development
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 3: Testing
# ============================================
FROM development AS testing

# Install test dependencies
RUN poetry install --with dev --no-root

# Copy test files
COPY tests/ ./tests/

# Run tests
CMD ["pytest", "-v", "--cov=src", "--cov-report=term-missing"]

# ============================================
# Stage 4: Production
# ============================================
FROM base AS production

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install only production dependencies
RUN poetry install --only main --no-root --no-ansi

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Run Alembic migrations on startup
CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4"]

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
