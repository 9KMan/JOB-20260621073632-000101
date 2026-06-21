# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POOL_MODE=transaction

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
COPY --chown=1000:1000 pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install -e . \
    && rm -rf /var/cache/pip/*

# Copy application code
COPY --chown=1000:1000 . .

# Switch to non-root user
USER apuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]
