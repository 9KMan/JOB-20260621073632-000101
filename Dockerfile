# Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
FROM base as builder

COPY --from=python:3.11-slim /requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r /requirements.txt

# Production image
FROM base

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy project files
COPY . /app

# Create non-root user
RUN addgroup --system --gid 1001 apautomation && \
    adduser --system --uid 1001 --ingroup apautomation --shell /bin/bash apautomation

# Set ownership
RUN chown -R apautomation:apautomation /app

# Switch to non-root user
USER apautomation

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
