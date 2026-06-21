# Phase 5: Testing & Operations — PLAN-01
## Finaro AP Automation

---

## 1. Phase Overview

**Phase:** 5 — Testing & Operations  
**Type:** Test Suite + CI/CD + Monitoring  
**Priority:** HIGH (requires Phase 3 & 4)  
**Estimated Duration:** 25–40 hours  
**Deliverable:** Production-ready test suite, CI/CD pipeline, and operational tooling

---

## 2. Phase Overview

Phase 5 ensures the matching engine and API are production-ready through:
1. Comprehensive test coverage (unit, integration, e2e)
2. Golden dataset validation
3. CI/CD pipeline with automated testing
4. Docker-based deployment
5. Basic monitoring and alerting
6. Documentation completion

---

## 3. Test Strategy

### 3.1 Test Pyramid

```
        ┌─────────────┐
        │    E2E      │  ← 5% (critical user journeys)
        │   Tests     │
       ┌┴─────────────┴┐
       │  Integration  │  ← 25% (API, database)
       │    Tests      │
      ┌┴───────────────┴┐
      │     Unit         │  ← 70% (core logic)
      │     Tests        │
      └─────────────────┘
```

### 3.2 Test Coverage Targets

| Layer | Target | Files |
|-------|--------|-------|
| Unit Tests | ≥ 80% | Core matching engine, validators, services |
| Integration Tests | ≥ 70% | API endpoints, database operations |
| E2E Tests | Critical paths | Login → Create Invoice → Match |

---

## 4. Test Structure

### 4.1 Unit Tests

```
tests/
├── unit/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── core/
│   │   ├── __init__.py
│   │   ├── test_engine.py       # MatchingEngine tests
│   │   ├── test_matchers/
│   │   │   ├── __init__.py
│   │   │   ├── test_invoice.py
│   │   │   ├── test_po.py
│   │   │   ├── test_grn.py
│   │   │   └── test_line.py
│   │   ├── validators/
│   │   │   ├── __init__.py
│   │   │   ├── test_amount.py
│   │   │   ├── test_date.py
│   │   │   ├── test_quantity.py
│   │   │   └── test_currency.py
│   │   └── test_config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_invoices.py
│   │   ├── test_purchase_orders.py
│   │   ├── test_grns.py
│   │   └── test_matching.py
│   └── services/
│       ├── __init__.py
│       ├── test_auth_service.py
│       ├── test_matching_service.py
│       └── test_document_services.py
```

### 4.2 Integration Tests

```
tests/
├── integration/
│   ├── __init__.py
│   ├── conftest.py              # DB fixtures, test client
│   ├── test_api/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_invoices.py
│   │   ├── test_purchase_orders.py
│   │   ├── test_grns.py
│   │   └── test_matching.py
│   ├── test_database/
│   │   ├── __init__.py
│   │   ├── test_migrations.py
│   │   ├── test_repositories.py
│   │   └── test_transactions.py
│   └── test_matching/
│       ├── __init__.py
│       ├── test_end_to_end.py
│       └── test_golden_dataset.py
```

### 4.3 E2E Tests

```
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_matching_flow.py    # Login → Create → Match → Verify
│   └── test_crud_flows.py       # Full CRUD cycle
```

---

## 5. Golden Dataset

### 5.1 Purpose
A curated set of known match/non-match scenarios that serve as regression tests.

### 5.2 Dataset Structure
```python
# tests/fixtures/golden_dataset.py

GOLDEN_CASES = [
    {
        "id": "exact_match_001",
        "description": "Perfect match - all values within tolerance",
        "invoice": {...},
        "po": {...},
        "grn": {...},
        "expected": {
            "status": "MATCHED",
            "score": 100.0,
            "mismatch_reasons": []
        }
    },
    {
        "id": "supplier_mismatch_001",
        "description": "Invoice supplier differs from PO supplier",
        "invoice": {"supplier_id": "uuid-A"},
        "po": {"supplier_id": "uuid-B"},
        "grn": {...},
        "expected": {
            "status": "MISMATCHED",
            "has_blocking": True,
            "blocking_field": "supplier_id"
        }
    },
    {
        "id": "partial_delivery_001", 
        "description": "GRN quantity < PO quantity (2% tolerance)",
        "invoice": {...},
        "po": {"lines": [{"quantity": 100}]},
        "grn": {"lines": [{"quantity": 98}]},
        "expected": {
            "status": "PARTIAL",
            "score": 98.0
        }
    },
    # ... 20+ cases covering all rule sets
]
```

### 5.3 Golden Test Runner
```python
# tests/integration/test_matching/test_golden_dataset.py

import pytest
from tests.fixtures.golden_dataset import GOLDEN_CASES

class TestGoldenDataset:
    @pytest.mark.parametrize("case", GOLDEN_CASES)
    def test_golden_case(self, case, matching_engine):
        result = matching_engine.match(
            invoice_id=case["invoice"]["id"],
            po_id=case["po"]["id"],
            grn_id=case["grn"]["id"]
        )
        assert result.status == case["expected"]["status"]
        assert result.match_score == case["expected"]["score"]
```

---

## 6. CI/CD Pipeline

### 6.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml

name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/finaro_test
  JWT_SECRET_KEY: test-secret-key-for-ci

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff black
      - run: ruff check src/
      - run: black --check src/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: finaro_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: alembic upgrade head
      - run: pytest tests/ -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3

  docker:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t finaro:${{ github.sha }} .
      - run: docker save finaro:${{ github.sha }} > finaro.tar

  deploy-staging:
    runs-on: ubuntu-latest
    needs: docker
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - # Deploy to staging environment
        # (具体部署步骤根据实际基础设施)
```

### 6.2 Quality Gates

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Code Coverage | ≥ 80% | YES |
| Linting (ruff) | 0 errors | YES |
| Unit Tests | 100% pass | YES |
| Integration Tests | 100% pass | YES |
| Golden Dataset | 100% pass | YES |
| Docker Build | Success | YES |

---

## 7. Docker & Deployment

### 7.1 Production Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim AS base

FROM base AS builder
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

FROM base AS runtime
WORKDIR /app
COPY --from=builder /opt/poetry /opt/poetry
ENV PATH="/opt/poetry/bin:$PATH"
COPY . .
RUN addgroup -S app && adduser -S app -G app
USER app
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose (Production Stack)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    restart: always
    volumes:
      - postgres_prod:/var/lib/postgresql/data
    env_file:
      - .env.production
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - api

volumes:
  postgres_prod:
  redis_data:
```

---

## 8. Monitoring & Observability

### 8.1 Health Checks

```python
# src/api/routes/health.py

@router.get("/health")
async def health_check():
    db_status = "connected"
    try:
        await db.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": settings.app.version,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 8.2 Structured Logging

```python
# src/api/middleware/logging.py

import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "extra": getattr(record, "extra", {})
        })

# Usage
logger.info("Match completed", extra={
    "invoice_id": str(invoice_id),
    "match_score": float(score),
    "duration_ms": elapsed_ms
})
```

### 8.3 Basic Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `finaro.matches.total` | Counter | Total match operations |
| `finaro.matches.success` | Counter | Successful matches |
| `finaro.matches.failed` | Counter | Failed matches |
| `finaro.matches.duration` | Histogram | Match operation duration |
| `finaro.api.requests.total` | Counter | Total API requests |
| `finaro.api.latency` | Histogram | API latency by endpoint |

---

## 9. Documentation

### 9.1 README.md Structure

```markdown
# Finaro — AP Automation 3-Way Matching Engine

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker (optional)

### Installation

```bash
# Clone
git clone https://github.com/9KMan/JOB-20260621073632-000101
cd JOB-20260621073632-000101

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn src.api.main:app --reload
```

### Configuration

See `config.yaml` for all configurable options.

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run golden dataset
pytest tests/integration/test_matching/test_golden_dataset.py -v
```

### Docker

```bash
# Local development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture

[Include architecture diagram]

## License

MIT
```

---

## 10. Acceptance Criteria

### 10.1 Test Coverage

- [ ] Unit test coverage ≥ 80% for core matching engine
- [ ] All golden dataset cases pass
- [ ] Integration tests cover all API endpoints
- [ ] E2E tests cover critical user journeys

### 10.2 CI/CD

- [ ] GitHub Actions workflow runs on push/PR
- [ ] All quality gates enforced
- [ ] Docker image builds successfully
- [ ] Staging deployment automated

### 10.3 Documentation

- [ ] README.md complete with setup instructions
- [ ] API documented via OpenAPI/Swagger
- [ ] Architecture documented
- [ ] Configuration options documented

### 10.4 Operations

- [ ] Health endpoint operational
- [ ] Structured logging implemented
- [ ] Docker Compose works for local development
- [ ] Production Docker Compose defined

---

## 11. Out of Scope (Phase 5)

- Load testing / performance benchmarking
- Advanced APM (Application Performance Monitoring)
- Log aggregation (ELK stack)
- Feature flags / A/B testing infrastructure
- Advanced alerting rules

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Unit test coverage | ≥ 80% |
| Integration test coverage | ≥ 70% |
| Golden dataset pass rate | 100% |
| CI pipeline runs | Green on main |
| Documentation completeness | 100% of public APIs |
| Docker image size | < 300MB |

---

## 13. Files to Create

The following files must be created in Phase 5:

### Unit Tests
```
tests/unit/__init__.py
tests/unit/conftest.py
tests/unit/core/__init__.py
tests/unit/core/test_engine.py
tests/unit/core/test_matchers/__init__.py
tests/unit/core/test_matchers/test_invoice.py
tests/unit/core/test_matchers/test_po.py
tests/unit/core/test_matchers/test_grn.py
tests/unit/core/test_matchers/test_line.py
tests/unit/core/validators/__init__.py
tests/unit/core/validators/test_amount.py
tests/unit/core/validators/test_date.py
tests/unit/core/validators/test_quantity.py
tests/unit/core/validators/test_currency.py
tests/unit/core/test_config.py
tests/unit/api/__init__.py
tests/unit/api/test_auth.py
tests/unit/api/test_invoices.py
tests/unit/api/test_purchase_orders.py
tests/unit/api/test_grns.py
tests/unit/api/test_matching.py
tests/unit/services/__init__.py
tests/unit/services/test_auth_service.py
tests/unit/services/test_matching_service.py
tests/unit/services/test_document_services.py
```

### Integration Tests
```
tests/integration/__init__.py
tests/integration/conftest.py
tests/integration/test_api/__init__.py
tests/integration/test_api/test_auth.py
tests/integration/test_api/test_invoices.py
tests/integration/test_api/test_purchase_orders.py
tests/integration/test_api/test_grns.py
tests/integration/test_api/test_matching.py
tests/integration/test_database/__init__.py
tests/integration/test_database/test_migrations.py
tests/integration/test_database/test_repositories.py
tests/integration/test_database/test_transactions.py
tests/integration/test_matching/__init__.py
tests/integration/test_matching/test_end_to_end.py
tests/integration/test_matching/test_golden_dataset.py
```

### E2E Tests
```
tests/e2e/__init__.py
tests/e2e/conftest.py
tests/e2e/test_matching_flow.py
tests/e2e/test_crud_flows.py
```

### Fixtures
```
tests/fixtures/golden_dataset.py
tests/fixtures/__init__.py
```

### CI/CD
```
.github/workflows/ci.yml
.github/workflows/deploy-staging.yml (optional)
```

### Docker
```
Dockerfile
docker-compose.yml
docker-compose.prod.yml
nginx.conf
```

### Documentation
```
README.md
ARCHITECTURE.md
```

---

## 14. Phase Completion Checklist

Before considering Phase 5 complete:

- [ ] All tests passing (unit, integration, e2e)
- [ ] Golden dataset validation passes
- [ ] CI/CD pipeline green
- [ ] Docker images build and run
- [ ] README and API docs complete
- [ ] No critical security vulnerabilities
- [ ] Code review completed and merged to main
