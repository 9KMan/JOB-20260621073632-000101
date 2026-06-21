# Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.1.18

FROM base as builder

COPY --from=base /usr/local/bin/uv /usr/local/bin/uv
COPY --from=base /usr/local/lib/python3.11/site-packages /site-packages

ENV UV_LINK_MODE=copy
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
RUN uv sync --frozen --no-install-project

FROM base as production

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /site-packages /usr/local/lib/python3.11/site-packages

COPY . .

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /site-packages /usr/local/lib/python3.11/site-packages

COPY . .

CMD ["uv", "run", "uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
