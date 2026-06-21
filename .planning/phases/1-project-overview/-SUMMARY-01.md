# Phase 1 Summary — Project Overview
## FinaRo AP Automation Core Engine

---

**What it is:** A 3-way matching engine that reconciles invoices against purchase orders and delivery notes, routing each to Post, Review, or Exception based on a score.

**Key insight from engine diagrams:**
- The engine has **two logical layers** before scoring: anchoring (which PO?) and cascade matching (which line?)
- Delivery notes are accumulated in a **balances ledger** — posting requires confirmed receipt (hard rule)
- Every human confirmation **learns and promotes** future matches via `cross_ref` — this is the defensible IP
- The invoice–delivery note–PO relationship is **many-to-many** at the balance level, not document-to-document

**Technical stack:** Python · FastAPI · PostgreSQL · Docker · SQLAlchemy · Alembic · pytest

**Deliverables created in this phase:**
- `1-project-overview/PLAN-01.md` — full project overview
- `1-project-overview/-SUMMARY-01.md` — this summary
