// docs/architecture.md
# FinaRo — AP Automation Core Engine Architecture

## 1. Project Overview

**FinaRo** is a 3-Way Matching Engine designed for accounts payable automation. It performs automated matching between three core documents:

- **Purchase Orders (PO)** — The authoritative source of truth for procurement commitments
- **Invoices** — Supplier billing documents requesting payment
- **Delivery Notes (DN)** — Proof of delivery confirmations

The engine determines whether invoices should be auto-approved, flagged for human review, or rejected into a dispute queue.

---

## 2. Technical Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Testing | pytest, pytest-asyncio |
| Authentication | JWT (HS256), bcrypt |
| Containerization | Docker, docker-compose |

---

## 3. Architecture Layers

### Layer 1 — Anchoring

Layer 1 establishes the deterministic anchor for all downstream matching operations. This layer uses the Purchase Order as the single source of truth.

#### Anchoring Logic

1. When an invoice or delivery note arrives in the system, it is first processed through the anchor resolver.
2. The anchor resolver queries open (unfulfilled) POs by:
   - Supplier identifier (required match)
   - PO number/reference (required match)
   - Date range validation (PO date ± tolerance window)
3. If a single matching PO is found, that PO becomes the anchor for all subsequent matching.
4. If multiple candidates exist, the system selects by:
   - Highest line-item overlap percentage
   - Closest date proximity
   - Most recent creation timestamp as tiebreaker
5. If no anchor is found, the document is flagged as `UNANCHORED` and routed to human review.

#### Anchor Table Schema

