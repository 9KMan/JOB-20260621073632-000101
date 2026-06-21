# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache \
    fastapi \
    uvicorn[standard] \
    sqlalchemy[asyncio] \
    asyncpg \
    alembic \
    pydantic \
    pydantic-settings \
    python-jose[cryptography] \
    passlib[bcrypt] \
    python-multipart \
    greenlet \
    httpx \
    pytest \
    pytest-asyncio \
    pytest-cov

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
