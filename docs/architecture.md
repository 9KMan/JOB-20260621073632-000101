// docs/architecture.md
# FinaRo — AP Automation Core Engine Architecture

## Document Information

| Field | Value |
|---|---|
| Project | FinaRo — AP Automation Core Engine |
| Client | Finaro |
| Version | 1.0.0 |
| Status | Phase 1 — Project Overview |

---

## 1. System Overview

FinaRo is an automated 3-Way Matching Engine designed for accounts payable (AP) automation. The system performs intelligent matching between three core document types:

1. **Purchase Orders (PO)** — Authoritative source of procurement intent
2. **Invoices** — Supplier billing documents requesting payment
3. **Delivery Notes (DN)** — Proof of goods/services received

The engine determines whether payments should be automatically approved, held for human review, or flagged for dispute based on configurable matching rules and exception handling workflows.

---

## 2. Architecture Layers

The matching engine operates through three distinct layers, each building upon the previous to create a robust and transparent matching process.

### 2.1 Layer 1 — Anchoring

**Purpose:** Establish deterministic anchors for all downstream matching operations.

**Logic:**

