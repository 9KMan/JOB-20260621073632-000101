# FinaRo — AP Automation Core Engine

3-Way Matching Engine for Invoice × Delivery Note × Purchase Order reconciliation.

## Features

- **Layer 1 - PO Anchoring**: Uses Purchase Orders as single source of truth
- **Layer 2 - Cascade Matching**: Intelligent matching across invoices, POs, and delivery notes
- **Layer 3 - Balance Resolution**: Tracks partial matches and balances
- **Decision Routing**: Auto-approve, human review, or dispute workflows

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic migrations
- JWT Authentication

## Quick Start

### Using Docker

