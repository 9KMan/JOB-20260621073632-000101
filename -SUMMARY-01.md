# Technical Stack Summary — AP Automation Core Engine

## Quick Reference

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Auth | JWT HS256 + bcrypt | - |
| Testing | pytest + httpx | 8.1+ / 0.27+ |
| Container | Docker + docker-compose | latest |

## Project Root
`/home/deploy/squad/build-worker/JOB-20260621073632-000101/`

## Key Architecture Decisions

1. **Async-first**: All database operations use async SQLAlchemy 2.0
2. **UUID PKs**: All tables use UUID primary keys (not auto-increment)
3. **Layered Matching Engine**:
   - Layer 1: Anchoring (PO → Invoice)
   - Layer 2: Cascade (Line-level matching)
   - Layer 3: Balances (Ledger updates)
   - Layer 4: Scoring (Decision routing)
   - Layer 5: Learning (cross_ref promotion)

4. **Configuration**: Environment variables via pydantic-settings
5. **Testing**: Unit tests for services, integration tests for matching flow

## Environment Variables Required

