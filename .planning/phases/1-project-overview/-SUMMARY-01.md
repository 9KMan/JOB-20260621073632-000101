// .planning/phases/1-project-overview/-SUMMARY-01.md
# FinaRo AP Automation Core Engine — Executive Summary

## Project Overview

**Client:** Finaro  
**Project:** AP Automation Core Engine (3-Way Matching)  
**Budget:** $14,250–$21,375 (150–225 hrs @ $95/hr)  
**Timeline:** 4–8 weeks

---

## The Problem

Accounts Payable teams manually reconcile invoices against POs and delivery notes. This is:

- **Error-prone** — manual comparison leads to payment mistakes
- **Slow** — hours per invoice, especially with discrepancies
- **Not scalable** — volume grows, headcount doesn't

---

## The Solution: FinaRo

FinaRo automates 3-way matching between:

| Document | Confirms |
|---|---|
| Purchase Order | What was ordered |
| Delivery Note | What was received |
| Invoice | What was billed |

**Output:** One decision per invoice → **Post**, **Review**, or **Flag**

---

## How It Works

### Step 1: Anchor to PO
Find which Purchase Order(s) this invoice belongs to:
- Primary: PO number on invoice
- Fallback: Supplier + date/amount window → ranked candidates

### Step 2: Match Line Items (Cascade)
For each invoice line, try methods in order of reliability:

| Level | Method | Reliability |
|---|---|---|
| 1 | Supplier ref → SKU (learned) | High |
| 2 | EAN / barcode | High |
| 3 | Internal SKU | High |
| 4 | Description fuzzy + price | Medium |
| 5 | Price + quantity | Low |
| 6 | Line amount | Low |

### Step 3: Verify Receipt
**Hard rule:** No invoice posted without confirmed goods receipt.

### Step 4: Calculate Balance
- `received = Σ delivery notes` per PO line
- `invoiced = Σ invoices` per PO line
- Clear when `received ≥ invoiced`

### Step 5: Score-Based Decision

| Score | Decision |
|---|---|
| ≥ 85% | Auto-approve → Post to ERP |
| 60–85% | 1-click review |
| < 60% | Exception → Human review |

---

## Learning Loop

Every human confirmation is stored and **promotes that match**:

