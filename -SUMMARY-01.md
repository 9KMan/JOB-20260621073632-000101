// -SUMMARY-01.md
# Phase 2 Summary — Technical Stack

## Quick Reference

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (HS256) + bcrypt |
| Testing | pytest + pytest-asyncio |
| Container | Docker + docker-compose |

## Key Architecture Decisions

1. **UUID Primary Keys** — All tables use UUIDs, not auto-increment
2. **Async-First** — SQLAlchemy async engine, async FastAPI endpoints
3. **Layered Services** — Anchoring → Cascade → Scoring → Learning
4. **Versioned API** — All routes under `/api/v1/`
5. **Environment Config** — All settings via pydantic-settings

## Project Structure

