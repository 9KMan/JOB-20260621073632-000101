# Phase 2 — Technical Stack Summary
## AP Automation Core Engine — FinaRo

---

## Quick Reference

| Component | Choice | Version |
|-----------|--------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Auth | JWT (HS256) + bcrypt | - |
| Testing | pytest | 8.1+ |
| Container | Docker | - |

---

## Configuration (Environment Variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/ap_automation` | DB connection |
| `JWT_SECRET_KEY` | (required) | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `THRESHOLD_HIGH` | `90` | Auto-approve threshold (%) |
| `THRESHOLD_MID` | `70` | 1-click review threshold (%) |
| `THRESHOLD_LOW` | `50` | Exception threshold (%) |
| `TOLERANCE_PRICE` | `5` | Price match tolerance (%) |
| `TOLERANCE_QTY` | `10` | Quantity match tolerance (%) |

---

## API Routes (`/api/v1/`)

| Domain | Endpoints |
|--------|-----------|
| `invoices` | POST /, GET /, GET /{id}, PATCH /{id} |
| `purchase_orders` | POST /, GET /, GET /{id} |
| `delivery_notes` | POST /, GET /, GET /{id} |
| `matching` | POST /trigger, GET /decision/{invoice_id} |
| `exceptions` | GET /, POST /resolve, POST /dismiss |

---

## Data Models

| Model | Description |
|-------|-------------|
| `Invoice` | Invoice header + lines with status |
| `PurchaseOrder` | PO header + lines |
| `DeliveryNote` | DN header + lines |
| `BalanceLedger` | Per-PO-line balance tracking |
| `CrossRef` | Learning loop / confirmed match history |

---

## Matching Engine Layers

| Layer | Service | Purpose |
|-------|---------|---------|
| 1 | `anchoring` | PO header-level matching |
| 2 | `cascade` | Line-level matching cascade |
| 3 | `scoring` | Score calculation + threshold routing |
| 4 | `learning` | Cross-ref promotion + history |

---

## Project Structure

