// Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python:3.11-slim / /

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml ./

RUN pip install --no-cache-dir .

COPY . .

RUN pip install pytest pytest-asyncio && \
    pip cache purge

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
