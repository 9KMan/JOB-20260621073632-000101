// -SUMMARY-01.md
# Phase 2 Summary — Technical Stack

## AP Automation Core Engine — FinaRo

---

## Stack Overview

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Auth | JWT (HS256) + bcrypt | - |
| Testing | pytest | 8.1+ |
| Container | Docker | - |

---

## Key Patterns

- **UUID Primary Keys** — All tables use UUIDs
- **Timestamps** — `created_at`/`updated_at` on all tables
- **Async First** — Full async database access via SQLAlchemy 2.0
- **Config via Env** — All secrets/config via environment variables
- **RESTful API** — Versioned endpoints `/api/v1/...`

---

## Configuration Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `JWT_SECRET_KEY` | - | HS256 signing secret |
| `THRESHOLD_HIGH` | 95 | Auto-approve score threshold |
| `THRESHOLD_MID` | 70 | 1-click review threshold |
| `THRESHOLD_LOW` | 40 | Exception threshold |
| `TOLERANCE_PRICE` | 5.0 | Price match tolerance (%) |
| `TOLERANCE_QTY` | 10.0 | Quantity match tolerance (%) |

---

## Project Structure

