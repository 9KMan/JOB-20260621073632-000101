# Phase 2 — Technical Stack Summary
## AP Automation Core Engine — FinaRo

---

## Stack Overview

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ (async) |
| Migrations | Alembic | 1.13+ |
| Auth | JWT (HS256) + bcrypt | - |
| Testing | pytest | 8.1+ |

---

## Key Patterns

- **UUIDs** for all primary keys
- **`created_at` / `updated_at`** on all tables
- **Async** SQLAlchemy sessions throughout
- **Pydantic v2** for request/response validation
- **RESTful** API with `/api/v1/` versioning

---

## Configuration via Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `JWT_SECRET_KEY` | - | HS256 signing secret |
| `THRESHOLD_HIGH` | 0.95 | Auto-approve cutoff |
| `THRESHOLD_MID` | 0.70 | 1-click review cutoff |
| `TOLERANCE_PRICE` | 0.02 | 2% price tolerance |
| `TOLERANCE_QTY` | 0.05 | 5% quantity tolerance |

---

## Project Structure

