// docs/architecture.md
# FinaRo — AP Automation Core Engine
## Architecture Documentation

---

## 1. Project Overview

**Project Name:** FinaRo — AP Automation Core Engine  
**Type:** 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order)  
**Client:** Finaro  
**Purpose:** Automated accounts payable processing with intelligent document matching

### Problem Statement

Manual invoice matching is error-prone, time-consuming, and creates bottlenecks in the accounts payable workflow. FinaRo automates the 3-way matching process between:
- **Purchase Orders (PO)** — Buyer-initiated orders to suppliers
- **Invoices** — Supplier billing documents
- **Delivery Notes (DN)** — Evidence of goods/services received

### Solution Approach

FinaRo implements a multi-layer matching engine that:
1. Anchors documents to Purchase Orders as the source of truth
2. Cascades matching across all document pairs with weighted scoring
3. Tracks and resolves partial matches through a balances ledger

---

## 2. Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python + FastAPI | REST API framework |
| Database | PostgreSQL | Primary datastore |
| ORM | SQLAlchemy | Database abstraction |
| Migrations | Alembic | Schema version control |
| Testing | pytest | Unit and integration tests |
| Containerization | Docker | Deployment packaging |
| Authentication | JWT (HS256) / bcrypt | API security |

### API Design

- RESTful endpoints with JSON request/response
- Versioned routes: `/api/v1/...`
- Middleware stack:
  - Request logging
  - Error handling (global exception handler)
  - CORS configuration
  - JWT authentication gate

---

## 3. Architecture Layers

### Layer 1 — Anchoring

**Purpose:** Establish deterministic anchors for all downstream matching

**Logic:**
1. When an invoice or delivery note arrives, the system attempts to match it against open (unfulfilled) Purchase Orders
2. Matching criteria for anchoring:
   - Supplier identification (exact match)
   - PO number reference (exact match)
   - Date proximity (configurable tolerance, e.g., ±7 days)

**Source of Truth:** The Purchase Order is treated as the authoritative document for pricing, quantities, and delivery expectations.

**Implementation:**
