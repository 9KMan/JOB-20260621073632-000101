// Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy dependency files
FROM base AS builder

# Install Python dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml ./
RUN uv sync --frozen --no-install-project

# Production image
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development image
FROM base AS development

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies in editable mode
RUN pip install -e ".[dev]" --no-cache-dir

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Development command with hot reload
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
