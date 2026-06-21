// -SUMMARY-01.md
# Technical Stack Summary — AP Automation Core Engine

## Technology Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI (async, OpenAPI)
- **Database:** PostgreSQL 15+ with PGBouncer
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Auth:** JWT (HS256) + bcrypt

## Key Architecture Decisions
- UUIDs for all primary keys
- `created_at`/`updated_at` timestamps on all entities
- RESTful API with `/api/v1/` versioning
- Business logic in dedicated service layer
- Layered matching engine: Anchoring → Cascade → Scoring → Learning

## Configuration
- All settings via environment variables
- Pydantic-settings for type-safe config management
- Configurable thresholds for auto-approve, review, and exceptions

## Testing Strategy
- Unit tests for all services (pytest)
- Integration tests for full matching flow
- FastAPI TestClient for API endpoint contracts
