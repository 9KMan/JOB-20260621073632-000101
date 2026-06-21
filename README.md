# FinaRo — AP Automation Core Engine

## Business Problem Solved

### The Challenge
AP (Accounts Payable) teams at mid-market companies face a recurring bottleneck: manual 3-way matching of supplier invoices against purchase orders and delivery notes. Finance staff spend hours cross-referencing spreadsheets, leading to delayed supplier payments, month-end bottlenecks, and costly errors that slip through to the wrong accounts.

### Our Solution
FinaRo automates the 3-way matching process:

1. **Deterministic 3-Way Matching** — Invoices validated against POs and delivery notes with configurable tolerances; all tolerances externalized to `config.yaml`
2. **Score-Based Routing** — Automatically routes to POST / REVIEW / EXCEPTION based on confidence thresholds (default: ≥0.95 → auto-post, ≥0.80 → human review)
3. **Learning Loop** — Human confirmations in `cross_ref` promote future matches from Level 4 → Level 1, improving accuracy for repeat suppliers and SKUs
4. **Real-Time Balance Ledger** — Per-PO and per-supplier running balances ensure an invoice never posts without a confirmed receipt
5. **REST API** — FastAPI-powered API for ERP integration, built-in Alembic migrations, JWT authentication

### Value Delivered
- **For AP Teams:** 80%+ straight-through processing rate, reduced manual review, faster month-end close
- **For Finance:** Full audit trail, deterministic routing, compliance-friendly decision records with explainable scores
- **For Suppliers:** Fewer disputes, faster approval cycles, transparent match/review status per invoice

---

## Tech Stack

- **Runtime:** Python 3.11+ with type hints
- **API Framework:** FastAPI with Pydantic v2 validation
- **Database:** PostgreSQL 15+ with SQLAlchemy 2.0 (async) + Alembic migrations
- **Authentication:** JWT (HS256) with bcrypt password hashing
- **Container:** Docker + docker-compose for local dev and production
- **Testing:** pytest with async test support, pytest-cov coverage

---

## Project Structure

```
.
├── api/                           # FastAPI route modules + schemas
│   ├── __init__.py
│   ├── schemas.py                 # Shared Pydantic request/response schemas
│   └── v1/
│       ├── __init__.py
│       ├── router.py              # API v1 router aggregator
│       ├── delivery_notes.py      # Delivery note CRUD + ingestion
│       ├── exceptions.py          # Custom API error handlers
│       ├── invoices.py            # Invoice CRUD + submission to engine
│       ├── matching.py           # 3-way match trigger + result retrieval
│       └── purchase_orders.py     # PO CRUD + line item access
├── core/                          # App-wide setup
│   ├── __init__.py
│   ├── config.py                  # Pydantic BaseSettings from environment
│   ├── database.py               # Async SQLAlchemy engine + session factory
│   └── security.py               # JWT token creation + password hashing
├── models/                        # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── balance_ledger.py          # Per-PO and per-supplier balance records
│   ├── base.py                    # Declarative base
│   ├── cross_ref.py              # Match confirmation + learning loop records
│   ├── delivery_note.py          # DeliveryNote + DeliveryNoteLine
│   ├── enums.py                  # InvoiceStatus, MatchResult, Decision enum
│   ├── invoice.py                 # Invoice + InvoiceLine
│   └── purchase_order.py          # PurchaseOrder + POLine
├── services/                      # Business logic
│   ├── __init__.py
│   ├── anchoring.py              # Layer 1: PO anchoring engine
│   ├── balances.py               # Balance ledger management
│   ├── cascade.py                # Layer 2: cascade matching (SKU/EAN → description → price×qty)
│   ├── learning.py               # Learning loop: confirm/promote cross_ref records
│   └── scoring.py                # Weighted score calculation (line-level 70%, amount 20%, date 10%)
├── workers/                       # Background job handlers
│   └── __init__.py
├── migrations/                    # Alembic migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/                         # pytest test suite
│   ├── conftest.py               # Shared fixtures (db, auth, sample data)
│   ├── unit/
│   │   ├── test_anchoring.py
│   │   ├── test_balances.py
│   │   ├── test_cascade.py
│   │   └── test_scoring.py
│   └── integration/
│       └── test_matching_flow.py  # Full 3-way match end-to-end
├── .env.example                   # Environment variable template
├── Dockerfile                     # Production container
├── docker-compose.yml             # Local dev (API + PostgreSQL)
├── alembic.ini                    # Alembic configuration
├── pyproject.toml                 # Project metadata + dependencies
└── main.py                        # FastAPI app bootstrap + lifespan
```

---

## Features

### 3-Way Matching Engine
- Deterministic 4-level cascade: cross_ref lookup → SKU/EAN match → description fuzzy match → price × quantity
- All tolerances externalized to `config.yaml` — no hardcoded thresholds
- Weighted scoring: line-level 70%, amount 20%, date 10%

### Score-Based Routing
- `score ≥ THRESHOLD_POST` (default 0.95) → auto-posted
- `score ≥ THRESHOLD_REVIEW` (default 0.80) → queued for human review
- `score < THRESHOLD_REVIEW` → exception workflow

### Learning Loop
- Human confirmation in `cross_ref` promotes future matches: Level 4 → Level 1
- Supplier + SKU granularity — learns per-supplier pricing quirks
- Soft-delete preserves full audit trail

### Balance Ledger
- Per-PO and per-supplier running balances always reflect current state
- Hard rule: invoice never posts without confirmed receipt
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
uv run uvicorn main:app --reload --port 8080
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

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |

---

## Database Schema

**Core tables:** `users`, `invoices`, `invoice_lines`, `purchase_orders`, `po_lines`, `delivery_notes`, `delivery_note_lines`, `cross_ref`, `balance_ledger`, `settings`

SQLAlchemy manages migrations in `migrations/versions/`. All financial amounts use `NUMERIC(12, 4)` for precision.

---

## Built by: KMan | AI-Augmented Engineering Factory
