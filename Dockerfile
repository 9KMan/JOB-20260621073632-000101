# Dockerfile
FROM python:3.11-slim as base

# Set environment variables
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
RUN groupadd --gid 1000 apuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home apuser

WORKDIR /app

# Install Python dependencies
COPY --chown=apuser:apuser pyproject.toml ./
RUN pip install --no-cache-dir --user -e . || true

# Copy application source
COPY --chown=apuser:apuser src/ ./src/
COPY --chown=apuser:apuser migrations/ ./migrations/
COPY --chown=apuser:apuser alembic.ini ./

# Create necessary directories
RUN mkdir -p /home/apuser/logs && chown apuser:apuser /home/apuser/logs

# Switch to non-root user
USER apuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
