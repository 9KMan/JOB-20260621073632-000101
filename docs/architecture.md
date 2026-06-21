// docs/architecture.md
# FinaRo — AP Automation Core Engine

## Architecture Documentation

---

## 1. Project Identity

| Field | Value |
|---|---|
| Project Name | FinaRo — AP Automation Core Engine |
| Client | Finaro |
| Type | 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order) |
| Tier | PREMIUM |
| Budget | $14,250–$21,375 (150–225 hrs @ $95/hr) |
| Timeline | 4–8 weeks |
| GitHub | https://github.com/9KMan/JOB-20260621073632-000101 |
| Rate | $95/hr |

---

## 2. Technical Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0+ |
| Migrations | Alembic |
| Authentication | JWT (HS256) |
| Password Hashing | bcrypt |
| Testing | pytest, pytest-asyncio |
| Containerization | Docker, docker-compose |
| API Documentation | OpenAPI/Swagger (auto-generated) |

---

## 3. Architecture Overview

The FinaRo AP Automation Core Engine implements a 3-way matching system for accounts payable automation. The system matches Invoices, Delivery Notes (GRN/Goods Receipt Notes), and Purchase Orders using a multi-layer matching architecture.

### 3.1 High-Level Architecture Diagram

