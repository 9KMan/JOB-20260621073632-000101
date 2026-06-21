# Phase 2 Summary: Technical Stack

## AP Automation Core Engine — FinaRo

---

## Tech Stack at a Glance

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ (async) |
| Migrations | Alembic | 1.13+ |
| Auth | JWT (HS256) + bcrypt | - |
| Container | Docker | - |

---

## Key Decisions

1. **Async-first**: All DB operations use `asyncpg` + `asyncio`
2. **UUID PKs**: All entities use UUIDs as primary keys
3. **Pydantic V2**: Settings and schemas via `pydantic-settings`
4. **Versioned API**: All routes under `/api/v1/`
5. **Configurable thresholds**: Match decision thresholds via env vars

---

## Project Layout

