# Phase 2 — Technical Stack Summary

## AP Automation Core Engine — FinaRo

### Technology Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI (async, Pydantic-first)
- **Database:** PostgreSQL 15+ with PGBouncer
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Auth:** JWT (HS256) + bcrypt

### Key Design Decisions
- UUIDs for all primary keys
- `created_at`/`updated_at` timestamps on all tables
- RESTful API with `/api/v1/` versioning
- Configurable matching thresholds via env vars
- Service layer for business logic isolation

### Project Structure
