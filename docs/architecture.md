# FinaRo — AP Automation Core Engine Architecture

## 1. Executive Summary

FinaRo is a 3-Way Matching Engine designed to automate the reconciliation of Invoices, Delivery Notes (GRN), and Purchase Orders (PO). The system provides intelligent matching with weighted scoring, partial match handling, and human-in-the-loop verification for edge cases.

### Key Capabilities

- **3-Way Matching**: Automatic reconciliation of Invoice × Delivery Note × Purchase Order
- **Weighted Scoring**: Multi-criteria matching algorithm (line-level 70%, amount 20%, date 10%)
- **Partial Match Handling**: Balances ledger for split shipments, partial invoices, and multi-delivery scenarios
- **Decision Routing**: Automated approval, human review queue, and dispute escalation
- **Learning Loop**: Human confirmations feed back into future matching decisions

---

## 2. System Architecture

