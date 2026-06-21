// .planning/phases/1-project-overview/PLAN-01.md
# Phase 1 — Project Overview
## AP Automation Core Engine — FinaRo

---

## 1. Phase Overview

**Phase:** 1 of N
**Subject:** Project Overview
**Goal:** Establish shared understanding of what FinaRo is, what problem it solves, and what success looks like — before any code is written.

---

## 2. Project Identity

| Field | Value |
|---|---|
| Project name | FinaRo — AP Automation Core Engine |
| Client | Finaro |
| Type | 3-Way Matching Engine (Invoice × Delivery Note × Purchase Order) |
| Tier | PREMIUM |
| Budget | $14,250–$21,375 (150–225 hrs @ $95/hr) |
| Timeline | 4–8 weeks |
| GitHub | https://github.com/9KMan/JOB-20260621073632-000101 |
| Rate | $95/hr |

---

## 3. Technical Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Testing | pytest |
| Containerization | Docker |
| Authentication | JWT (HS256) or bcrypt |

### Architecture Overview

### Layer 1 — Anchoring

Layer 1 uses the PO as the single source of truth for anchoring. When an invoice or delivery note arrives, the system first tries to match it against open POs by supplier and PO number. This establishes a deterministic anchor for all downstream matching.

### Layer 2 — Cascade Matching

Layer 2 performs cascade matching: invoice ↔ PO, then delivery note ↔ PO, then invoice ↔ delivery note. Each match is scored with weighted criteria (line-level 70%, amount 20%, date 10%).

### Layer 3 — Balance Resolution

Layer 3 tracks partial matches and balances across all three document types using a balances ledger. This allows the system to handle partial shipments, split invoices, and multi-delivery scenarios.

### Decision Routing

All matches route through a decision engine: CONFIRMED → AUTO-APPROVE, PENDING → HUMAN_REVIEW, REJECTED → DISPUTE. Human confirmations in the cross-reference table feed back into future matching (learning loop).

---

## 4. Files to Create

docs/architecture.md

---

## 5. Phase Completion Criteria

- [ ] Architecture overview written and accurate
- [ ] All 3 layers described with correct logic
- [ ] Decision routing clearly explained
- [ ] No placeholder TODOs in architecture documentation
