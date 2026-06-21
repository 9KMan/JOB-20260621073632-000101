# Phase 7 — Documentation
## FinaRo AP Automation Core Engine

---

## 1. Phase Overview

**Phase:** 7 of 7
**Subject:** Documentation
**Goal:** Produce all remaining user-facing and developer documentation: the README (final version), API reference, architecture decision records (ADRs), and a comprehensive deployment guide. This phase closes out the project with a production-ready documentation suite.

---

## 2. What Gets Documented

This phase covers four documentation deliverables:

| Deliverable | Audience | Purpose |
|---|---|---|
| `README.md` (final) | Developers, DevOps, PM | First-impression overview + setup |
| `API.md` | API consumers, frontend team | Endpoint reference with request/response examples |
| `ARCHITECTURE.md` | Architects, senior engineers | Design decisions, data flow diagrams, ADRs |
| `DEPLOYMENT.md` | DevOps, infrastructure team | Docker, environment config, secrets management |

---

## 3. README.md — Final Version

**Location:** `README.md` (root)

### 3.1 Structure

```markdown
# FinaRo — AP Automation Core Engine

## Business Problem Solved

### The Challenge
[1–2 paragraphs: what AP teams / accountants struggle with — manual 3-way matching, spreadsheet errors, supplier disputes, month-end bottlenecks]

### Our Solution
FinaRo automates the 3-way matching process:

1. **Automated 3-Way Matching** — Invoices matched against POs and delivery notes with configurable tolerances
2. **Score-Based Routing** — Automatically routes to POST / REVIEW / EXCEPTION based on confidence thresholds
3. **Learning Loop** — Human confirmations improve future match accuracy for repeat suppliers and SKUs
4. **Real-Time Balances** — Per-PO and per-supplier balance ledgers always reflect current state
5. **REST API** — FastAPI-powered API for ERP integration, built-in Alembic migrations

### Value Delivered
- **For AP Teams:** 80%+ straight-through processing rate, reduced manual review, faster month-end close
- **For Finance:** Full audit trail, deterministic routing, compliance-friendly decision records
- **For Suppliers:** Fewer disputes, faster approval cycles, transparent status tracking

---

## Tech Stack

- **Runtime:** Python 3.11+ with type hints
- **API Framework:** FastAPI with Pydantic v2 validation
- **Database:** PostgreSQL 15+ with SQLAlchemy 2.0 (async) + Alembic migrations
- **Authentication:** JWT (HS256) with bcrypt password hashing
- **Container:** Docker + docker-compose for local dev and production
- **Testing:** pytest with async test support, factory_boy fixtures

---

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app bootstrap + lifespan
│   ├── config.py               # Settings from environment (Pydantic BaseSettings)
│   ├── database.py             # Async SQLAlchemy engine + session factory
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── invoice.py
│   │   ├── purchase_order.py
│   │   ├── delivery_note.py
│   │   ├── cross_ref.py
│   │   ├── balance.py
│   │   └── user.py
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── invoice.py
│   │   ├── matching.py
│   │   └── learning.py
│   ├── api/                    # Route modules
│   │   ├── __init__.py
│   │   ├── invoices.py
│   │   ├── purchase_orders.py
│   │   ├── delivery_notes.py
│   │   ├── matching.py
│   │   ├── learning.py
│   │   ├── balances.py
│   │   ├── users.py
│   │   └── health.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── matching.py         # 3-way matching engine
│   │   ├── learning.py         # Learning loop service
│   │   └── balance.py          # Balance ledger service
│   └── core/                   # Security, JWT, auth
│       ├── __init__.py
│       ├── security.py
│       └── dependencies.py
├── migrations/                 # Alembic migration scripts
│   └── versions/
├── tests/                      # pytest test suite
│   ├── conftest.py             # Shared fixtures
│   ├── unit/
│   └── integration/
├── docs/                       # Additional documentation
│   ├── api.md
│   ├── architecture.md
│   └── deployment.md
├── docker-compose.yml          # Local dev (API + PostgreSQL)
├── Dockerfile                  # Production container
├── .env.example                # Environment variable template
├── alembic.ini                 # Alembic configuration
└── pyproject.toml              # Project metadata + dependencies
```

---

## Features

### 3-Way Matching Engine
- Deterministic 4-level cascade: cross_ref → SKU/EAN → Description fuzzy → Price × Qty
- Weighted scoring: line-level 70%, amount 20%, date 10%
- All tolerances externalized to `config.yaml` — no hardcoded thresholds

### Score-Based Routing
- `score ≥ THRESHOLD_POST` (default 0.95) → auto-posted
- `score ≥ THRESHOLD_REVIEW` (default 0.80) → queued for human review
- `score < THRESHOLD_REVIEW` → exception workflow

### Learning Loop
- Human confirmation in `cross_ref` table promotes future matches: Level 4 → Level 1
- Supplier + SKU granularity — learns per-supplier pricing quirks
- Soft-delete preserves audit trail

### Balance Ledger
- Per-PO and per-supplier running balances
- Invoice never posts without confirmed receipt (hard rule)
- Delivery notes and invoices have independent arrival cycles

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- `uv` package manager

### 1. Clone & Install

```bash
git clone https://github.com/9KMan/JOB-20260621073632-000101.git
cd JOB-20260621073632-000101
uv sync
```

### 2. Environment Variables

Create `.env` from the example:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://finaro:***@localhost:5432/finaro` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | `openssl rand -hex 32` |
| `THRESHOLD_POST` | Auto-post confidence threshold | `0.95` |
| `THRESHOLD_REVIEW` | Human-review threshold | `0.80` |
| `ENVIRONMENT` | `development` or `production` | `development` |

### 3. Start Database

```bash
docker compose up -d db
```

Wait for PostgreSQL to be ready (~5s), then run migrations:

```bash
alembic upgrade head
```

### 4. Start API

```bash
uv run uvicorn app.main:app --reload --port 8080
```

API server runs at `http://localhost:8080`. Health check:

```bash
curl http://localhost:8080/api/health
```

### 5. Run Tests

```bash
uv run pytest tests/ -v
```

---

## API Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login, returns access + refresh tokens |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/auth/logout` | Invalidate refresh token |

### Invoices
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/invoices` | Submit a new invoice |
| `GET` | `/api/v1/invoices` | List invoices (filterable by status, supplier) |
| `GET` | `/api/v1/invoices/{id}` | Get invoice details |
| `GET` | `/api/v1/invoices/{id}/status` | Get invoice status + match result |
| `POST` | `/api/v1/invoices/{id}/match` | Trigger manual re-match |
| `POST` | `/api/v1/invoices/{id}/submit` | Submit invoice to matching engine |

### Purchase Orders
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/purchase-orders` | Create a PO |
| `GET` | `/api/v1/purchase-orders` | List POs |
| `GET` | `/api/v1/purchase-orders/{id}` | Get PO details |
| `GET` | `/api/v1/purchase-orders/{id}/lines` | Get PO line items |

### Delivery Notes
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/delivery-notes` | Record a delivery note |
| `GET` | `/api/v1/delivery-notes` | List delivery notes |
| `GET` | `/api/v1/delivery-notes/{id}` | Get delivery note details |

### Matching Engine
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/match` | Run 3-way match for an invoice |
| `GET` | `/api/v1/match/{invoice_id}/result` | Get match result for an invoice |

### Learning Loop
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/learning/confirm` | Confirm a match pair (promotes future matches) |
| `GET` | `/api/v1/learning/promoted/{supplier_id}/{invoice_sku}` | Get promoted matches for supplier+SKU |
| `GET` | `/api/v1/learning/supplier/{supplier_id}` | Get all learning records for a supplier |
| `DELETE` | `/api/v1/learning/{cross_ref_id}` | Remove a learning record (soft-delete) |

### Balances
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/balances/po/{po_id}` | Get balance ledger for a PO |
| `GET` | `/api/v1/balances/supplier/{supplier_id}` | Get balance ledger for a supplier |

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |

---

## Database Schema

**Core tables:** `users`, `invoices`, `invoice_lines`, `purchase_orders`, `po_lines`, `delivery_notes`, `delivery_note_lines`, `cross_ref`, `balances`, `settings`

SQLAlchemy manages migrations in `migrations/versions/`. All financial amounts use `NUMERIC(12, 4)` for precision.

---

## Built by: KMan | AI-Augmented Engineering Factory
```

### 3.2 Quality Checklist

- [ ] All code blocks are syntax-highlighted (bash, python, json, yaml)
- [ ] All links (to API.md, DEPLOYMENT.md) are relative and correct
- [ ] Environment variable table has: name, default, required?, description
- [ ] "Business Problem Solved" section is written for a non-technical reader
- [ ] Quick Start works from a fresh clone in < 5 minutes

---

## 4. API.md — Endpoint Reference

**Location:** `docs/api.md` (create `docs/` directory)

### 4.1 Structure

```markdown
# FinaRo API Reference

## Overview
[Base URL, version, authentication method]

## Authentication
[Bearer token / JWT — describe header]

## Endpoints

### Health
GET /health

### Invoice Lifecycle
POST   /api/v1/invoices
GET    /api/v1/invoices
GET    /api/v1/invoices/{id}
GET    /api/v1/invoices/{id}/status
POST   /api/v1/invoices/{id}/match
POST   /api/v1/invoices/{id}/submit

### PO Management
POST   /api/v1/purchase-orders
GET    /api/v1/purchase-orders
GET    /api/v1/purchase-orders/{id}
GET    /api/v1/purchase-orders/{id}/lines

### Delivery Notes
POST   /api/v1/delivery-notes
GET    /api/v1/delivery-notes
GET    /api/v1/delivery-notes/{id}

### Matching Engine
POST   /api/v1/match
GET    /api/v1/match/{invoice_id}/result

### Learning Loop
POST   /api/v1/learning/confirm
GET    /api/v1/learning/promoted/{supplier_id}/{invoice_sku}
GET    /api/v1/learning/supplier/{supplier_id}
DELETE /api/v1/learning/{cross_ref_id}

### Balances
GET    /api/v1/balances/po/{po_id}
GET    /api/v1/balances/supplier/{supplier_id}

### Users (for review flow)
GET    /api/v1/users/me
GET    /api/v1/users/{id}
```

### 4.2 Per-Endpoint Template

```markdown
### POST /api/v1/invoices

**Description:** Submit a new invoice for processing.

**Authentication:** Required (Bearer token)

**Request body:**
```json
{
  "supplier_id": "uuid",
  "invoice_number": "string",
  "invoice_date": "2026-01-01",
  "lines": [
    {
      "sku": "string",
      "description": "string",
      "quantity": 10.0,
      "unit_price": 25.50,
      "tax_rate": 0.21,
      "uom": "EA"
    }
  ]
}
```

**Response:** `202 Accepted`
```json
{
  "id": "uuid",
  "status": "submitted",
  "submitted_at": "2026-06-21T10:00:00Z",
  "match_result": null
}
```

**Error responses:**
| Status | Condition |
|---|---|
| 400 | Malformed JSON |
| 401 | Missing or invalid token |
| 422 | Validation error (missing fields) |
| 500 | Internal server error |

---
```

### 4.3 Error Response Schema

All error responses follow this shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {
        "field": "lines[0].quantity",
        "issue": "must be a positive number"
      }
    ]
  },
  "request_id": "uuid"
}
```

---

## 5. ARCHITECTURE.md — Design Decisions & Data Flow

**Location:** `docs/architecture.md`

### 5.1 Structure

```markdown
# FinaRo Architecture

## System Overview
[High-level block diagram — services, databases, external integrations]

## Data Flow Diagrams

### Invoice Processing Flow
```
Client → POST /api/v1/invoices
       → Invoice created (status=submitted)
       → Match engine invoked
       → Score computed
       → Decision: POST / REVIEW / EXCEPTION
       → Result written to invoice.match_result
```

### Learning Loop Flow
[same loop diagram as in Phase 6 plan]

### 3-Way Matching Flow
```
Invoice lines
    │
    ├─ Level 0: cross_ref (promoted matches)
    ├─ Level 1: SKU / EAN
    ├─ Level 2: Description fuzzy + price
    └─ Level 3: Price + quantity
              │
              ▼
        MatchResult(score, po_line_id, method)
              │
              ▼
        Compare: invoiced vs. received vs. ordered
              │
              ▼
        Final Decision
```

## Architecture Decision Records (ADRs)

### ADR-001: PostgreSQL as Primary Datastore
**Context:** Need relational storage for invoices, POs, delivery notes with ACID guarantees.
**Decision:** PostgreSQL 15 with PGBouncer connection pooling.
**Consequences:** Strong consistency; requires migration management via Alembic.

### ADR-002: UUID Primary Keys
**Context:** Distributed systems, multiple services inserting records.
**Decision:** UUID v4 for all primary keys (server-generated via `gen_random_uuid()`).
**Consequences:** No ID collision; not sequential (no information leakage in URLs).

### ADR-003: Score-Based Routing
**Context:** Need deterministic, auditable routing for compliance.
**Decision:** Thresholds stored in `settings` table; overridable per supplier.
**Consequences:** Simple to reason about; requires threshold calibration per deployment.

### ADR-004: Learning Loop via cross_ref Table
**Context:** Human review data must persist and influence future matches.
**Decision:** Separate `cross_ref` table with soft-delete, `(supplier_id, invoice_sku)` unique constraint.
**Consequences:** Self-improving accuracy; requires FK discipline to avoid orphaned rows.

### ADR-005: Append-Only BigQuery Writes (no upsert)
**Context:** Audit trail, replay capability.
**Decision:** Write-only with deduplication key `(source_id, ingested_at)`.
**Consequences:** History preserved; must handle late-arriving data carefully.

### ADR-006: JWT (HS256) for API Authentication
**Context:** Internal service-to-service and user authentication.
**Decision:** HS256 with secret key in environment; short expiry (15 min access, 7 day refresh).
**Consequences:** Simple; shared secret must be rotated. Not suitable for multi-service distributed systems without a token broker.

## Database Schema Summary

[Entity-Relationship summary or table listing all tables with their primary keys and key relationships]

## External Integrations

| Integration | Protocol | Notes |
|---|---|---|
| ERP System | REST API (outbound) | Invoice posting, PO pull |
| LLM Service | HTTP/httpx | AI tagging in ETL pipeline |
| Looker Studio | BigQuery connection | Reporting (out of scope for core engine) |
```

---

## 6. DEPLOYMENT.md — Docker & Environment Guide

**Location:** `docs/deployment.md`

### 6.1 Structure

```markdown
# FinaRo Deployment Guide

## Prerequisites
- Docker 24+
- Docker Compose v2
- PostgreSQL 15 (or via Docker)
- GCP project (if using BigQuery for reporting)

## Container Architecture

### Services
| Service | Image | Port | Description |
|---|---|---|---|
| api | finaro-api | 8080 | FastAPI application |
| db | postgres:15 | 5432 | PostgreSQL database |
| migrations | finaro-api | — | Alembic migration runner (one-shot) |
| airflow-scheduler | apache/airflow:2.8 | 8080 | Airflow scheduler (optional) |

### Environment Variables

#### Required
| Variable | Example | Description |
|---|---|---|
| DATABASE_URL | postgresql://finaro:finaro@db:5432/finaro | PostgreSQL connection string |
| SECRET_KEY | `openssl rand -hex 32` | JWT signing key |
| GCP_PROJECT_ID | my-gcp-project | BigQuery project (optional) |
| GCP_BIGQUERY_DATASET | finaro_prod | BigQuery dataset name |

#### Optional
| Variable | Default | Description |
|---|---|---|
| LOG_LEVEL | INFO | Logging verbosity |
| AIRFLOW_HOME | /opt/airflow | Airflow home directory |
| CACHE_TTL_SECONDS | 120 | Metric cache TTL |

### Secrets Management
[Describe how to manage SECRET_KEY in production: Kubernetes secrets, AWS SM, etc.]

## Docker Compose

### Development
```bash
docker-compose up -d          # starts api + db
docker-compose logs -f api    # tail API logs
```

### Production
```bash
# Build
docker build -t finaro-api:latest .

# Run migrations
docker-compose run --rm migrations alembic upgrade head

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Database Migrations

```bash
# Run pending migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "Add cross_ref table"

# Rollback
alembic downgrade -1
```

## Health Checks

```bash
# API health
curl http://localhost:8080/health

# Expected response
{"status": "healthy", "timestamp": "...", "service": "finaro-api"}
```

## Monitoring

[Prometheus metrics endpoint: GET /metrics]
[Structured JSON logging with request_id traceability]

## Backup & Recovery

- PostgreSQL: standard pg_dump / pg_restore
- point-in-time recovery: WAL archiving to S3/GCS
- RTO: < 1 hour
- RPO: < 5 minutes (WAL-E or pg_backoff)
```

---

## 7. Documentation Style Guide

To maintain consistency across all documents:

| Rule | Example |
|---|---|
| Use active voice | "The service writes the record" not "Records are written by the service" |
| Code blocks must specify language | ` ```python ` not just ` ``` ` |
| Use `code` for file names, env vars, and API paths | `DATABASE_URL`, `/api/v1/invoices` |
| Use **bold** for UI labels and important warnings | **WARNING:** |
| One sentence per line in lists (no wrapping) | Keeps diffs readable |
| Screenshots only for UI; all diagrams in ASCII/Mermaid | Keeps docs diffable |

---

## 8. Tools & Generation

Documents are written manually (not auto-generated from code) to ensure narrative quality. However, the following can be generated from code and included:

- API schema from FastAPI `openapi.json` → converted to `API.md`
- SQLAlchemy table list → extracted for `ARCHITECTURE.md`

```bash
# Extract OpenAPI schema
curl http://localhost:8080/openapi.json > docs/openapi.json

# Generate API.md from OpenAPI (optional — review output manually)
npx @redocly/cli build-docs docs/openapi.json
```

---

## 9. Acceptance Criteria

- [ ] **DOC-01**: `README.md` exists at root with all required sections (Business Problem, Architecture, Tech Stack, Quick Start, Project Structure, Environment Variables)
- [ ] **DOC-02**: `README.md` Quick Start works from a fresh clone in < 5 minutes
- [ ] **DOC-03**: `docs/api.md` documents every endpoint in the API with request/response examples
- [ ] **DOC-04**: `docs/api.md` includes error response schema and per-status-code table
- [ ] **DOC-05**: `docs/architecture.md` contains all 6 ADRs listed in this plan
- [ ] **DOC-06**: `docs/architecture.md` contains data flow diagrams for invoice processing, learning loop, and matching cascade
- [ ] **DOC-07**: `docs/deployment.md` covers Docker Compose (dev + prod), environment variables, secrets management, migrations, and backup/recovery
- [ ] **DOC-08**: All `.md` files have valid Markdown syntax (headers, code blocks, tables)
- [ ] **DOC-09**: All links between docs are relative and resolve correctly
- [ ] **DOC-10**: `docs/` directory is created and contains: `api.md`, `architecture.md`, `deployment.md`
- [ ] **DOC-11**: `SPEC.md` is updated to reflect any final design decisions from implementation

---

## 10. Phase 7 Deliverables

1. `7-documentation/PLAN-01.md` — this document
2. `7-documentation/-SUMMARY-01.md` — condensed executive summary
3. `README.md` — final version with all sections
4. `docs/api.md` — full API reference
5. `docs/architecture.md` — architecture decisions and data flow diagrams
6. `docs/deployment.md` — Docker and deployment guide
7. `SPEC.md` — updated with any final decisions from implementation

---

## 11. Files to Create

The following files must be created to implement this phase:

### Documentation Files
| File | Purpose |
|------|---------|
| `README.md` | Final README with Business Problem, Architecture overview, Features, Tech Stack, Quick Start, Project Structure, Environment Variables |
| `docs/api.md` | Full API reference with all endpoints, request/response examples, and error schemas |
| `docs/architecture.md` | Architecture Decision Records (ADRs 001–006), data flow diagrams, database schema summary |
| `docs/deployment.md` | Docker & environment guide covering dev/prod compose, env vars, secrets, migrations, monitoring, backup |

### Specification Update
| File | Purpose |
|------|---------|
| `SPEC.md` | Updated with any final design decisions from implementation phases |

---

## 12. Dependencies & Blockers

|| Dependency | Blocking | Notes |
||---|---|---|
|| All previous phases (1–6) | Yes | All code must be written before docs are finalized |
|| API endpoints finalized | Yes | API.md cannot be written until routes are locked |
|| Test suite passing | Partial | README "Quick Start" requires passing tests to be accurate |
