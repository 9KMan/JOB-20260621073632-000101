// Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY core/ ./core/
COPY models/ ./models/
COPY api/ ./api/
COPY services/ ./services/
COPY workers/ ./workers/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - development
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
