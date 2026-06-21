// docs/architecture.md
# FinaRo — AP Automation Core Engine Architecture

## 1. Project Identity

| Field | Value |
|---|---|
| Project Name | FinaRo — AP Automation Core Engine |
| Client | Finaro |
| Type | 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order) |
| Tier | PREMIUM |
| Budget | $14,250–$21,375 (150–225 hrs @ $95/hr) |
| Timeline | 4–8 weeks |
| Rate | $95/hr |

### Core Problem Statement

Accounts Payable (AP) departments face significant challenges when reconciling incoming invoices against purchase orders (POs) and delivery notes. Manual 3-way matching is time-consuming, error-prone, and creates bottlenecks in the procurement-to-payment cycle.

FinaRo automates this process by implementing an intelligent 3-way matching engine that:
- Anchors all documents against their corresponding Purchase Orders
- Performs cascade matching across all document types
- Tracks and resolves partial matches through a balances ledger
- Routes exceptions to appropriate resolution workflows

---

## 2. Technical Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0+ |
| Migrations | Alembic |
| Authentication | JWT (HS256) |
| Testing | pytest |
| Containerization | Docker, Docker Compose |

---

## 3. System Architecture

### 3.1 High-Level Architecture

