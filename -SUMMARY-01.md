# Technical Stack Summary — AP Automation Core Engine

## Stack Overview
| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (HS256) + bcrypt |

## Configuration
All settings via environment variables:
- `DATABASE_URL` — PostgreSQL connection
- `JWT_SECRET_KEY` — HS256 signing secret
- `THRESHOLD_*` — Matching decision thresholds
- `TOLERANCE_*` — Price/quantity match tolerances

## Key Models
- Invoice, PurchaseOrder, DeliveryNote, BalanceLedger, CrossRef

## Service Layers
1. **Anchoring** — PO anchoring logic
2. **Cascade** — Line-matching cascade
3. **Balances** — Ledger service
4. **Scoring** — Score calculation + threshold routing
5. **Learning** — Cross-reference learning

## API Endpoints
| Domain | Path |
|---|---|
| Invoices | `/api/v1/invoices` |
| Purchase Orders | `/api/v1/purchase-orders` |
| Delivery Notes | `/api/v1/delivery-notes` |
| Matching | `/api/v1/matching` |
| Exceptions | `/api/v1/exceptions` |
| Balances | `/api/v1/balances` |

## Dependencies
