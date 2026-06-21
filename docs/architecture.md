// docs/architecture.md
# FinaRo — AP Automation Core Engine Architecture

## 1. Project Overview

**Project Name:** FinaRo — AP Automation Core Engine  
**Client:** Finaro  
**Type:** 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order)  
**Budget:** $14,250–$21,375 (150–225 hrs @ $95/hr)  
**Timeline:** 4–8 weeks

FinaRo is an Accounts Payable automation engine that performs intelligent 3-way matching between invoices, delivery notes (DN), and purchase orders (PO). The system establishes a deterministic anchor using POs as the single source of truth, performs cascade matching across document pairs, and resolves partial matches through a balances ledger mechanism.

---

## 2. Technical Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Testing | pytest |
| Containerization | Docker, docker-compose |
| Authentication | JWT (HS256), bcrypt |
| API | RESTful JSON endpoints |

---

## 3. System Architecture

