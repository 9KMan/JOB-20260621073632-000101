# Phase 1 — Project Overview
## AP Automation Core Engine — FinaRo

---

## 1. Phase Overview

**Phase:** 1 of N
**Subject:** Project Overview
**Goal:** Establish shared understanding of what FinaRo is, what problem it solves, and what success looks like — before any code is written.

---

## 2. Project Identity

| Field | Value |
|---|---|
| Project name | FinaRo — AP Automation Core Engine |
| Client | Finaro |
| Type | 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order) |
| Tier | PREMIUM |
| Budget | $14,250–$21,375 (150–225 hrs @ $95/hr) |
| Timeline | 4–8 weeks |
| GitHub | https://github.com/9KMan/JOB-20260621073632-000101 |

---

## 3. Problem Statement

Accounts Payable teams manually reconcile incoming invoices against purchase orders (POs) and delivery notes. This is error-prone, slow, and does not scale as invoice volume grows.

FinaRo automates this reconciliation using a **3-way matching engine** that compares three sources:

| Source | Entry method |
|---|---|
| Purchase Order (PO) | ERP integration |
| Delivery Note | ERP integration or OCR |
| Invoice | ERP integration or OCR |

The engine converges these three documents line-by-line into a single decision: **Post**, **Review**, or **Flag as Exception**.

---

## 4. Engine Logic — High-Level Flow

### 4.1 Two Paths Before Matching

```
Invoice received
      │
      ├─ No PO found ──────────────────► Non-PO Route (out of scope for engine spec)
      │
      └─ Has PO(s) ──► Layer 1: Anchoring ──► Layer 2: Matching Cascade ──► Decision
```

### 4.2 Layer 1 — Anchoring to a PO

Before touching any line items, the engine narrows which PO(s) the invoice belongs to.

- **Primary path:** PO number explicitly on the invoice
- **Fallback:** Supplier + open POs bounded by date/amount window
- **Result:** Ranked candidate POs (not forced single match)

### 4.3 Layer 2 — Line-Matching Cascade

For each invoice line, methods are tried in cascade (most reliable → least):

| Level | Method | Score |
|---|---|---|
| 1 | `ref_proveedor → SKU` via cross_ref | High |
| 2 | EAN / barcode | High |
| 3 | Internal SKU on invoice | High |
| 4 | Description fuzzy + price proximity | Mid (needs confirmation) |
| 5 | Price + quantity | Low |
| 6 | Line amount (within tolerance) | Low |

- Every human confirmation is stored in `cross_ref` and promotes that match to Level 1 for the supplier's next invoice
- **Learning loop:** Over time, description matching becomes key matching — this is FinaRo's defensible IP

### 4.4 Delivery Note Ingestion

- Delivery notes arrive via ERP integration (goods receipt) or OCR at the dock
- They feed the **balances ledger** (`cant_recibida += received`)
- The balances ledger determines if goods were received before allowing invoice posting

> **Hard rule:** A product invoice is never posted without confirmed receipt.

### 4.5 Balances Ledger — Many-to-Many Logic

The invoice–delivery note–PO relationship is **many-to-many**:

- `received = Σ delivery notes` per PO line
- `invoiced = Σ invoices` per PO line
- A PO line **clears** when `received ≥ invoiced` within tolerance and price fits

This handles:
- Partial deliveries (several delivery notes per line)
- Consolidated invoices (one invoice across several POs)

### 4.6 Score-Based Decision

After line matching + comparison (price, quantity, UoM, tax):

| Score band | Action |
|---|---|
| ≥ high threshold | Auto-approve → post to ERP |
| Mid band | 1-click review (feeds learning loop) |
| Below low threshold | Typed exception → human |

Thresholds are configurable globally and overridable per supplier.

---

## 5. Scope

### In Scope
- 3-way matching engine (PO, delivery note, invoice)
- REST API backend (FastAPI)
- PostgreSQL database
- Learning loop via `cross_ref` persistence
- Balance ledger
- Score-based routing (post / review / exception)
- Docker containerization
- Unit tests

### Out of Scope
- Mobile apps
- Multi-tenant / white-label customization
- Performance optimization at 1M+ user scale
- Non-PO invoice route (documented separately in process doc)
- OCR pipeline (acknowledged as separate build cost)
- ERP integration implementation (treated as external)

---

## 6. Success Criteria

- [ ] Application builds and runs without errors
- [ ] Core matching engine implemented as described
- [ ] Learning loop correctly persists and promotes matches
- [ ] Basic unit tests for key features
- [ ] README with setup instructions
- [ ] Docker configuration for deployment

---

## 7. Architecture Constraints

- **Backend:** Python (FastAPI) REST API
- **Database:** PostgreSQL with connection pooling
- **Auth:** JWT (HS256) or bcrypt
- **ORM:** SQLAlchemy + Alembic migrations
- **Testing:** pytest
- **Container:** Docker + docker-compose

---

## 8. Phase 1 Deliverables

This phase produces:
1. `PLAN-01.md` — this document
2. `-SUMMARY-01.md` — condensed executive summary
