// docs/architecture.md
# FinaRo — AP Automation Core Engine

## Architecture Documentation

---

## 1. Project Overview

**Project Name:** FinaRo — AP Automation Core Engine  
**Type:** 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order)  
**Purpose:** Automate the accounts payable matching process by comparing invoices against purchase orders and delivery notes, reducing manual review and accelerating approval workflows.

### Problem Statement

Traditional AP workflows require accountants to manually match invoices against purchase orders (POs) and delivery notes. This process is:

- **Time-consuming:** Manual comparison of line items across documents
- **Error-prone:** Human error in amount calculations and quantity matching
- **Inconsistent:** Varying tolerance thresholds and approval criteria
- **Bottlenecked:** Sequential review creates approval delays

### Solution

FinaRo automates the 3-way matching process through a layered architecture that:

1. Anchors all documents to their originating Purchase Orders
2. Performs cascade matching with weighted scoring
3. Tracks balances across partial matches
4. Routes decisions through an intelligent decision engine

---

## 2. Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.11+ / FastAPI | REST API framework |
| Database | PostgreSQL 15+ | Primary datastore |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema version control |
| Authentication | JWT (HS256) | API authentication |
| Password Hashing | bcrypt | Secure credential storage |
| Testing | pytest | Unit and integration tests |
| Containerization | Docker | Deployment packaging |

### System Architecture

