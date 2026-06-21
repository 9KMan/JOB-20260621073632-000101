// -SUMMARY-01.md
# Phase 2 — Technical Stack Summary

## AP Automation Core Engine — FinaRo

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Web Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ (async) |
| Migrations | Alembic | 1.13+ |
| Connection Pooling | PGBouncer | Latest |
| Authentication | JWT (HS256) + bcrypt | — |
| Testing | pytest + pytest-asyncio | 8.1+ |

### Key Architecture Decisions

1. **UUID Primary Keys** — All entities use UUIDs for distributed-safe IDs
2. **Async-First** — SQLAlchemy async driver with asyncpg for non-blocking I/O
3. **Pydantic V2** — Schema validation with pydantic-settings for config management
4. **Layered Architecture** — API → Services → Models separation of concerns

### API Endpoints

| Domain | Operations |
|--------|------------|
| Invoices | POST /api/v1/invoices, GET /api/v1/invoices, GET /api/v1/invoices/{id} |
| Purchase Orders | POST /api/v1/purchase-orders, GET /api/v1/purchase-orders, GET /api/v1/purchase-orders/{id} |
| Delivery Notes | POST /api/v1/delivery-notes, GET /api/v1/delivery-notes, GET /api/v1/delivery-notes/{id} |
| Matching Engine | POST /api/v1/matching/trigger, GET /api/v1/matching/decisions/{invoice_id} |
| Exceptions | GET /api/v1/exceptions, POST /api/v1/exceptions/{id}/resolve, POST /api/v1/exceptions/{id}/dismiss |
| Balances Ledger | GET /api/v1/balances/{po_line_id} |

### Matching Engine Layers

1. **Layer 1 — Anchoring**: PO header-level matching (supplier, date range, total)
2. **Layer 2 — Cascade**: Line-by-line matching with configurable tolerances
3. **Scoring**: Weighted scoring with configurable thresholds
4. **Learning Loop**: Cross-reference table for pattern recognition

### Threshold Configuration

| Threshold | Default | Action |
|-----------|---------|--------|
| HIGH | 95 | Auto-approve |
| MID | 75 | 1-click review |
| LOW | 50 | Exception flagged |

### Environment Variables

- `DATABASE_URL` — PostgreSQL connection string
- `JWT_SECRET_KEY` — HS256 signing secret
- `THRESHOLD_HIGH/MID/LOW` — Scoring thresholds
- `TOLERANCE_PRICE/QTY` — Matching tolerance percentages

### Project Deliverables

- Complete FastAPI REST API with async SQLAlchemy
- PostgreSQL schema with Alembic migrations
- Docker containerization with docker-compose
- Unit + integration test suite
- Documentation (README + OpenAPI docs)
