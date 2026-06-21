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

