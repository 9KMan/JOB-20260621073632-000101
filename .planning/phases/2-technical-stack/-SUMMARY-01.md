# Phase 2 Summary — Technical Stack
## FinaRo AP Automation Core Engine

---

**Language:** Python 3.11+
**Framework:** FastAPI
**Database:** PostgreSQL + PGBouncer + SQLAlchemy 2.0 (async) + Alembic
**Auth:** JWT (HS256) + bcrypt
**Testing:** pytest + pytest-asyncio
**Container:** Docker + docker-compose

**Project structure:**
- `api/` — FastAPI routes + Pydantic schemas
- `models/` — SQLAlchemy ORM models
- `services/` — Business logic (anchoring, cascade, balances, scoring, learning)
- `core/` — Config, security, database session
- `migrations/` — Alembic versioned migrations
- `tests/` — Unit + integration tests

**Key design decisions:**
- UUID primary keys on all tables
- Async ORM throughout (sqlalchemy[asyncio] + asyncpg)
- PGBouncer for connection pooling
- Thresholds configurable globally + per supplier
- `cross_ref` table drives the learning loop

**Deliverables created in this phase:**
- `2-technical-stack/PLAN-01.md` — full technical stack spec
- `2-technical-stack/-SUMMARY-01.md` — this summary
