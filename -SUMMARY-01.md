# Phase 2 Summary — Technical Stack

## AP Automation Core Engine — FinaRo

### Technology Choices

| Component | Choice | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Connection Pooling | PGBouncer | - |
| Authentication | JWT (HS256) + bcrypt | - |
| Testing | pytest + pytest-asyncio | 8.1+ / 0.23+ |

### Configuration

All settings via environment variables using `pydantic-settings`:

- `DATABASE_URL` — PostgreSQL connection string
- `JWT_SECRET_KEY` / `JWT_ALGORITHM` — Token signing
- `THRESHOLD_HIGH` / `THRESHOLD_MID` / `THRESHOLD_LOW` — Decision thresholds
- `TOLERANCE_PRICE` / `TOLERANCE_QTY` — Matching tolerances

### Project Structure

