// Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VENV="/opt/pypoetry" \
    POETRY_CACHE_DIR="/opt/.cache" \
    PATH="$POETRY_VENV/bin:$PATH" \
    DOCKER_BUILDKIT=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Set working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root --extras "dev"

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup --system --gid 1001 apuser && \
    adduser --system --uid 1001 --ingroup apuser --shell /bin/bash apuser

# Change ownership of application files
RUN chown -R apuser:apuser /app

# Switch to non-root user
USER apuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
