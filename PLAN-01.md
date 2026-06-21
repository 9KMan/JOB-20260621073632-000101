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
| PK strategy | **UUIDs** | Per spec |

---

## 4. Authentication

| Component | Choice | Rationale |
|---|---|---|
| JWT | HS256 | Per spec |
| Password hashing | bcrypt | Per spec |

---

## 5. API Design

- **Style:** RESTful with JSON request/response
- **Versioning:** `/api/v1/...` route prefix
- **Middleware:** Logging, error handling, CORS
- **Schemas:** Pydantic models (FastAPI native)

---

## 6. Project Structure

