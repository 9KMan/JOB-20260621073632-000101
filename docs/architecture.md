// docs/architecture.md
# FinaRo — AP Automation Core Engine Architecture

## 1. Project Overview

**Project Name:** FinaRo — AP Automation Core Engine  
**Client:** Finaro  
**Type:** 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order)  
**Tier:** PREMIUM  
**Budget:** $14,250–$21,375 (150–225 hrs @ $95/hr)  
**Timeline:** 4–8 weeks  

### Problem Statement

Accounts Payable (AP) departments face significant challenges in manually matching invoices against purchase orders (POs) and delivery notes. Manual 3-way matching is time-consuming, error-prone, and creates bottlenecks in the procurement-to-payment workflow. FinaRo automates this process by implementing an intelligent 3-way matching engine that reduces manual intervention, accelerates approval cycles, and provides full auditability.

### Solution Overview

FinaRo is a RESTful API service that ingests invoices, delivery notes, and purchase orders, then performs automated 3-way matching using a layered architecture approach. The system scores matches based on configurable weighted criteria, handles partial matches and balance tracking, and routes decisions through an intelligent decision engine for auto-approval, human review, or dispute escalation.

---

## 2. Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.11+ | Core application logic |
| API Framework | FastAPI | RESTful API with automatic OpenAPI docs |
| Database | PostgreSQL 15+ | Primary datastore with JSONB support |
| ORM | SQLAlchemy 2.0 | Database abstraction and type-safe queries |
| Migrations | Alembic | Schema version control and migrations |
| Authentication | JWT (HS256) | Stateless API authentication |
| Password Hashing | bcrypt | Secure credential storage |
| Testing | pytest + pytest-asyncio | Unit and integration testing |
| Containerization | Docker + Docker Compose | Local development and production deployment |
| Connection Pooling | SQLAlchemy async with asyncpg | Non-blocking database connections |

---

## 3. Architecture Overview

