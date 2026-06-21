// -SUMMARY-01.md
# AP Automation Core Engine — Technical Stack Summary

## Overview

A Python-based accounts payable automation system that matches invoices against purchase orders and delivery notes using a multi-layer matching engine.

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Auth | JWT (HS256) + bcrypt | - |
| Testing | pytest + pytest-asyncio | 8.1+ |
| Container | Docker + docker-compose | - |

## Key Features

- **Invoice Processing:** Ingest, validate, and match invoices
- **PO Matching:** Multi-layer matching engine (anchoring → cascade → scoring)
- **Delivery Note Integration:** Three-way match support
- **Exception Handling:** Automated routing and resolution
- **Learning Loop:** Confidence improvement from confirmed matches
- **Balance Ledger:** Real-time PO line balance tracking

## Architecture Layers

