# Finaro — AP Automation 3-Way Matching Engine

## 1. Concept & Vision

Finaro is a B2B accounts-payable automation engine for the Spanish mid-market. It matches supplier invoices against purchase orders and delivery notes using a cascade matching algorithm, routing each invoice line to auto-post, 1-click review, or human exception. The matching engine is the defensible IP; ERP connectors and OCR pipelines are handled separately.

The platform exposes a FastAPI REST API. The matching engine is deterministic and auditable — every decision is logged, every exception is typed, and every human confirmation teaches the engine via a cross-reference learning table.

## 2. Technical Stack

- **Runtime:** Python 3.11+ with type hints throughout
- **API:** FastAPI (async) + Pydantic v2 for validation
- **Database:** PostgreSQL 15+ with async SQLAlchemy 2.0
- **Migrations:** Alembic
- **Testing:** pytest + pytest-asyncio
- **Container:** Docker + docker-compose (single `docker compose up` for dev/staging)
- **Observability:** Structured JSON logs; Prometheus-compatible `/metrics` endpoint

## 3. Architecture

### 3-Way Matching Flow

```
Invoice (integration or OCR)
  ↓
Layer 1: Anchor to PO
  ├─ Direct: invoice has PO number → link directly
  └─ Fallback: supplier + open POs + date/amount window → ranked candidates
       (if 0 candidates → non-PO route, out of scope for V1)
  ↓
Balances Ledger: received (Σ DNs) vs invoiced (Σ invoices) per PO line
  ↓
Layer 2: Cascade matching per invoice line
  Level 1: ref_proveedor → SKU (via cross_ref, supplier-specific)
  Level 2: EAN / barcode
  Level 3: internal SKU on invoice
  Level 4: Description fuzzy + price proximity  [never alone — always with price/quantity]
  Level 5: Price + quantity
  Level 6: Line amount within tolerance
  ↓
Score-based routing:
  High (≥0.85): auto-approve → post to ERP
  Mid (0.60–0.84): 1-click review → human confirms/corrects → updates cross_ref
  Low (<0.60): typed exception → human typed resolution
  ↓
Balances check before post:
  received ≥ invoiced within tolerance → clearable
  received < invoiced → partial / over-invoiced exception
```

### Learning Loop

Every human confirmation writes to `cross_ref` table: `(supplier_id, description_pattern → confirmed_SKU)`.
On next invoice from same supplier: Level-4 confirmed once → pair promoted to Level-1.
Level 4 never matches alone — always combined with price/quantity. This is a hard constraint.

### Data Model

**Tables:**
- `purchase_orders` — PO header + lines (read-only copy from ERP)
- `delivery_notes` — DN header + lines (from integration or OCR normalization)
- `invoices` — invoice header + lines (from integration or OCR normalization)
- `balances_ledger` — per PO line: accumulated `received` (Σ DNs) and `invoiced` (Σ invoices)
- `cross_ref` — learned matches: `(supplier_id, description_pattern) → confirmed_SKU`
- `match_results` — per invoice line: match decision, score, method, exceptions
- `exceptions` — typed exceptions awaiting human resolution
- `audit_log` — all state transitions for compliance

**Indexes:**
- `balances_ledger`: `(po_line_id, received, invoiced)`
- `cross_ref`: `(supplier_id, description_pattern)`
- `invoices`: `(po_number, supplier_id)`

## 4. API Design

### Invoice Lifecycle
```
POST /invoices              Submit invoice (header + lines) → returns match job ID
GET  /invoices/{id}         Get invoice status + line match results
GET  /invoices/{id}/lines/{line_id}/match  Get match detail for specific line
POST /invoices/{id}/confirm/{line_id}       1-click confirm: accept suggested match
POST /invoices/{id}/resolve/{line_id}       Resolve exception: override match
```

### Exception Queue
```
GET  /exceptions              List open exceptions (filterable by supplier, age, type)
POST /exceptions/{id}/resolve  Resolve exception (type + resolution data)
```

### Admin / Observability
```
GET  /balances/{po_line_id}   Get current balances for a PO line
GET  /audit/{invoice_id}       Audit trail for an invoice
GET  /health                   Liveness probe
GET  /ready                   Readiness (DB + cross_ref connectivity)
```

All endpoints: JWT-authenticated. Roles: `engineer` (read), `approver` (confirm/resolve), `admin` (audit, cross_ref management).

## 5. Production Requirements

- **Idempotency:** Invoice submission with same idempotency key returns existing result, doesn't duplicate
- **Graceful degradation:** If `cross_ref` is unavailable, cascade continues without it (warn, don't fail)
- **Rate limiting:** Configurable per-tenant
- **Dead-letter queue:** OCR results that fail normalization are stored and retryable
- **Secrets:** All credentials via environment variables — no hardcoding
- **Testing:** ≥90% line coverage on matching engine; all cascade branches tested
