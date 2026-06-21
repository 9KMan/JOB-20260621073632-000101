// -SUMMARY-01.md
# Phase 2 Summary — Technical Stack

## Stack Overview
| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0 (async) |
| Migrations | Alembic | 1.13+ |
| Auth | JWT (HS256) + bcrypt | - |

## Key Architecture Decisions

### Database
- UUID primary keys (not auto-increment)
- `created_at` / `updated_at` timestamps on all tables
- Async SQLAlchemy with connection pooling via PGBouncer
- Indexes on FKs and high-cardinality columns

### API
- RESTful endpoints under `/api/v1/`
- Pydantic request/response validation
- Auto-generated OpenAPI docs at `/docs`

### Testing
- pytest for unit and integration tests
- Async test fixtures with pytest-asyncio
- FastAPI TestClient for API tests

## Configuration
Environment variables manage all settings:
- `DATABASE_URL` — PostgreSQL connection
- `JWT_SECRET_KEY` — HS256 signing secret
- `THRESHOLD_*` — Matching decision thresholds
- `TOLERANCE_*` — Price/quantity tolerance %

## Project Structure
