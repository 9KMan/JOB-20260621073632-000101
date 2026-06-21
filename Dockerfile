# Dockerfile
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POOL_MODE=transaction

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 apgroup && \
    useradd --uid 1000 --gid apgroup --shell /bin/bash --create-home apuser

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -r pyproject.toml[all] 2>/dev/null || \
    pip install --no-cache-dir \
    fastapi>=0.110.0 \
    uvicorn[standard]>=0.29.0 \
    sqlalchemy[asyncio]>=2.0.25 \
    asyncpg>=0.29.0 \
    alembic>=1.13.1 \
    pydantic>=2.6.0 \
    pydantic-settings>=2.2.0 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    python-multipart>=0.0.9 \
    email-validator>=2.1.0 \
    greenlet>=3.0.0 \
    pytest>=8.1.0 \
    pytest-asyncio>=0.23.0 \
    httpx>=0.27.0

# Copy application code
COPY . .

# Set ownership
RUN chown -R apuser:apgroup /app

USER apuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
