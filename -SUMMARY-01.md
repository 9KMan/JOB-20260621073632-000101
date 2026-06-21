# Phase 2 — Technical Stack Summary
## AP Automation Core Engine — FinaRo

---

## Stack at a Glance

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.110+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Database | PostgreSQL | 15+ |
| Connection Pooling | PGBouncer | — |
| Migrations | Alembic | 1.13+ |
| Validation | Pydantic v2 | 2.6+ |
| Auth | JWT (HS256) + bcrypt | — |
| Testing | pytest + pytest-asyncio | 8.1+ |
| Container | Docker | — |

---

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | DB connection |
| `JWT_SECRET_KEY` | — | HS256 signing secret |
| `THRESHOLD_HIGH` | `0.95` | Auto-approve score |
| `THRESHOLD_MID` | `0.70` | 1-click review score |
| `THRESHOLD_LOW` | `0.40` | Exception threshold |
| `TOLERANCE_PRICE` | `0.02` | Price match tolerance (2%) |
| `TOLERANCE_QTY` | `0.05` | Quantity match tolerance (5%) |

---

## Project Structure

