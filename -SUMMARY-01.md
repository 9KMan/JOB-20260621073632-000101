# Technical Stack Summary — AP Automation Core Engine

## Core Stack
| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Container | Docker |

## Key Dependencies
- `fastapi>=0.110`, `uvicorn[standard]>=0.29`
- `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`
- `alembic>=1.13`, `pydantic>=2.6`, `pydantic-settings>=2.2`
- `python-jose[cryptography]>=3.3`, `passlib[bcrypt]>=1.7`
- `pytest>=8.1`, `pytest-asyncio>=0.23`, `httpx>=0.27`

## Architecture Patterns
- RESTful API with `/api/v1/` versioning
- UUID primary keys on all tables
- `created_at`/`updated_at` timestamps
- Async SQLAlchemy sessions
- Pydantic request/response validation

## Matching Engine Layers
1. **Anchoring** — PO header-to-invoice anchoring
2. **Cascade** — Line-level matching with tolerance
3. **Balances** — Ledger tracking per PO line
4. **Scoring** — Match confidence scoring
5. **Learning** — Cross-reference table for confirmed matches

## Configuration
- Environment variables via `pydantic-settings`
- Configurable thresholds: `THRESHOLD_HIGH`, `THRESHOLD_MID`, `THRESHOLD_LOW`
- Tolerances: `TOLERANCE_PRICE`, `TOLERANCE_QTY`
