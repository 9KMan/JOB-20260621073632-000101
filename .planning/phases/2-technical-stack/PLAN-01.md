# Phase 2 — Technical Stack
## AP Automation Core Engine — FinaRo

---

## 1. Phase Overview

**Phase:** 2 of N
**Subject:** Technical Stack
**Goal:** Define the technology choices, project structure, and implementation patterns that will guide all subsequent phases.

---

## 2. Language & Framework

### Language
| Choice | Version | Rationale |
|---|---|---|
| **Python** | 3.11+ | Per spec; strong ecosystem for data-heavy logic |

### Web Framework
| Choice | Rationale |
|---|---|
| **FastAPI** | Per spec; async-capable, auto-generated OpenAPI, Pydantic-first validation |

---

## 3. Database

| Component | Choice | Rationale |
|---|---|---|
| Primary datastore | **PostgreSQL 15+** | Per spec; relational integrity for financial data |
| Connection pooling | **PGBouncer** | Per spec; reduces connection overhead |
| ORM | **SQLAlchemy 2.0** (async) | Type-safe, supports async, mature |
| Migrations | **Alembic** | Per spec; SQLAlchemy-native migration tool |
| PK strategy | **UUIDs** (not auto-increment) | Per spec |

### Key Database Patterns
- `created_at` / `updated_at` timestamps on all tables
- Soft-delete pattern where appropriate
- Indexes on foreign keys and high-cardinality columns
- `ON DELETE CASCADE` for FK constraints
- Many-to-many via junction tables
- Eager loading for nested relationships in API

---

## 4. Authentication

| Component | Choice | Rationale |
|---|---|---|
| JWT | HS256 | Per spec |
| Password hashing | bcrypt | Per spec |
| Token expiry | Configurable | Short-lived access + refresh tokens |

---

## 5. API Design

- **Style:** RESTful with JSON request/response
- **Versioning:** `/api/v1/...` route prefix
- **Middleware:** Logging, error handling, CORS
- **Schemas:** Pydantic models (FastAPI native)
- **OpenAPI:** Auto-generated docs at `/docs`

### Anticipated Endpoints (Phase TBD)

| Domain | Operations |
|---|---|
| Invoices | ingest, list, get, update status |
| Purchase Orders | ingest (from ERP), list, get |
| Delivery Notes | ingest (ERP/OCR), list, get |
| Matching Engine | trigger match, get decision |
| Exceptions | list, resolve, dismiss |
| Balances Ledger | get per PO line |
| Learning / cross_ref | view confirmed matches |

---

## 6. Project Structure

```
/home/deploy/squad/build-worker/JOB-20260621073632-000101/
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py          # API router aggregator
│   │   ├── invoices.py        # Invoice endpoints
│   │   ├── purchase_orders.py # PO endpoints
│   │   ├── delivery_notes.py  # Delivery note endpoints
│   │   ├── matching.py        # Matching engine endpoints
│   │   └── exceptions.py      # Exception handling endpoints
│   └── schemas.py             # Shared Pydantic request/response models
├── models/
│   ├── __init__.py
│   ├── base.py                # SQLAlchemy declarative base
│   ├── invoice.py
│   ├── purchase_order.py
│   ├── delivery_note.py
│   ├── balance_ledger.py
│   ├── cross_ref.py           # Learning loop table
│   └── enums.py               # Status enums, decision types
├── services/
│   ├── __init__.py
│   ├── anchoring.py           # Layer 1: PO anchoring logic
│   ├── cascade.py             # Layer 2: Line matching cascade
│   ├── balances.py            # Balances ledger service
│   ├── scoring.py             # Score calculation + threshold routing
│   └── learning.py            # cross_ref learning/promotion logic
├── workers/
│   ├── __init__.py
│   └── matching.py            # Background matching jobs (if needed)
├── migrations/
│   └── versions/              # Alembic migration scripts
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   ├── unit/
│   │   ├── test_anchoring.py
│   │   ├── test_cascade.py
│   │   ├── test_balances.py
│   │   └── test_scoring.py
│   └── integration/
│       └── test_matching_flow.py
├── core/
│   ├── __init__.py
│   ├── config.py              # Environment / settings
│   ├── security.py            # JWT + bcrypt utilities
│   └── database.py            # DB session management
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── README.md
```

---

## 7. Configuration

Managed via environment variables / `.env`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `PGBOUNCER_HOST` | PGBouncer host (if used) |
| `JWT_SECRET_KEY` | HS256 signing secret |
| `JWT_ALGORITHM` | HS256 |
| `THRESHOLD_HIGH` | Auto-approve threshold (configurable) |
| `THRESHOLD_MID` | 1-click review threshold (configurable) |
| `THRESHOLD_LOW` | Exception threshold (configurable) |
| `TOLERANCE_PRICE` | Price match tolerance % |
| `TOLERANCE_QTY` | Quantity match tolerance % |

---

## 8. Docker Setup

- **Dockerfile:** Python 3.11 slim base, production-ready
- **docker-compose.yml:** PostgreSQL + PGBouncer + API service
- Local dev should run entirely via `docker-compose up`

---

## 9. Testing Strategy

| Level | Tool | Scope |
|---|---|---|
| Unit | pytest | Services: anchoring, cascade, balances, scoring |
| Integration | pytest + test DB | Full matching flow |
| API | FastAPI TestClient | Endpoint contracts |

Minimum coverage target: key matching logic, threshold routing, learning loop.

---

## 10. Dependencies (Python)

```toml
# pyproject.toml (key entries)
fastapi>=0.110
uvicorn[standard]>=0.29
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29
alembic>=1.13
pydantic>=2.6
pydantic-settings>=2.2
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
python-multipart>=0.0.9
pytest>=8.1
pytest-asyncio>=0.23
httpx>=0.27
```

---

## 11. Phase 2 Deliverables

This phase produces:
1. `PLAN-01.md` — this document
2. `-SUMMARY-01.md` — condensed technical stack summary

> **Note:** This plan defines the stack and structure. Implementation details for each API domain, service, and data model will be detailed in subsequent phase plans.
