# -SUMMARY-01.md

# Phase 2 Technical Stack Summary — AP Automation Core Engine

## Stack Overview
- **Language:** Python 3.11+
- **Framework:** FastAPI (async, Pydantic-first)
- **Database:** PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Auth:** JWT HS256 + bcrypt
- **Testing:** pytest + pytest-asyncio

## Key Files
- `pyproject.toml` — Dependencies
- `docker-compose.yml` — PostgreSQL + PGBouncer + API
- `core/config.py` — Environment via pydantic-settings
- `core/database.py` — Async SQLAlchemy session management
- `models/` — Invoice, PO, DeliveryNote, BalanceLedger, CrossRef
- `services/` — Anchoring, Cascade, Balances, Scoring, Learning
- `api/v1/` — RESTful endpoints with versioning

## Thresholds (Configurable)
- `THRESHOLD_HIGH` — Auto-approve
- `THRESHOLD_MID` — 1-click review
- `THRESHOLD_LOW` — Exception

## Tolerances (Configurable)
- `TOLERANCE_PRICE` — Price match tolerance %
- `TOLERANCE_QTY` — Quantity match tolerance %
