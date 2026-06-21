// docs/architecture.md
# FinaRo — AP Automation Core Engine Architecture

## 1. Executive Summary

FinaRo is a 3-Way Matching Engine designed to automate the reconciliation of Invoices, Delivery Notes (GRN/Goods Receipt), and Purchase Orders. The system establishes a Purchase Order as the anchor point, performs cascade matching across document pairs, and resolves partial matches through a balances ledger before routing decisions to appropriate workflows.

---

## 2. System Architecture Overview

