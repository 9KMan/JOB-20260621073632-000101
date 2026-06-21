// docs/architecture.md
# FinaRo — AP Automation Core Engine

## Architecture Documentation

---

## 1. System Overview

FinaRo is an Accounts Payable (AP) Automation Core Engine that implements a **3-Way Matching** system. The system validates invoices against delivery notes and purchase orders to ensure financial accuracy and prevent fraudulent payments.

### Core Problem Statement

Traditional AP workflows require manual verification of:
- **Invoice** (from supplier) — what we're being asked to pay
- **Delivery Note** (from logistics) — what was actually delivered
- **Purchase Order** (from procurement) — what we agreed to buy

Manual matching is error-prone, time-consuming, and scales poorly. FinaRo automates this process with a three-layer matching engine.

---

## 2. Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.11+ / FastAPI | REST API, async processing |
| Database | PostgreSQL 15+ | Primary datastore |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema version control |
| Authentication | JWT (HS256) / bcrypt | Secure API access |
| Testing | pytest / pytest-asyncio | Unit & integration tests |
| Containerization | Docker / Docker Compose | Deployment & dev environment |
| Connection Pooling | SQLAlchemy async pool | Efficient DB connections |

---

## 3. Architecture Layers

### Layer 1 — PO Anchoring

**Purpose:** Establish deterministic anchors for all downstream matching operations.

**Logic Flow:**

