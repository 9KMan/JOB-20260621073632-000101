# Phase 3: Core Matching Engine — PLAN-01
## Finaro AP Automation

---

## 1. Phase Overview

**Phase:** 3 — Core Engine  
**Type:** Deterministic 3-Way Matching Logic  
**Priority:** CRITICAL (blocking all downstream phases)  
**Estimated Duration:** 40–60 hours  
**Deliverable:** Production-ready Python module for invoice-PO-delivery-note matching

---

## 2. Problem Statement

Spanish mid-market businesses (supermarkets, distribution, manufacturing) need to automatically match supplier invoices against purchase orders (POs) and delivery notes (GRNs/Albaranes). Manual matching is slow, error-prone, and expensive.

**Core Requirement:** A deterministic matching engine that:
1. Takes an invoice, PO, and delivery note as input
2. Returns a definitive match/non-match result with line-level confidence
3. Explains *why* a match succeeded or failed
4. Handles common real-world variances (partial deliveries, price tolerances, currency)

---

## 3. Technical Architecture

### 3.1 Module Location
```
src/
├── core/
│   ├── __init__.py
│   ├── engine.py          # Main matching orchestrator
│   ├── matchers/
│   │   ├── __init__.py
│   │   ├── invoice.py     # Invoice field extraction & normalization
│   │   ├── po.py          # PO field extraction & normalization
│   │   ├── grn.py         # Delivery note (GRN/Albarán) extraction
│   │   └── line.py        # Line-item matching logic
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── amount.py      # Amount/tolerance validation
│   │   ├── date.py        # Date sequence validation
│   │   ├── quantity.py    # Quantity tolerance handling
│   │   └── currency.py    # Currency validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py    # Base document model (Invoice, PO, GRN)
│   │   ├── line.py        # Line item model
│   │   ├── match_result.py # Match result model
│   │   └── mismatch.py    # Mismatch detail model
│   └── config.py          # Tolerance thresholds, matching rules
├── schemas/                # Pydantic models (if FastAPI in scope)
└── tests/
    └── unit/
        └── test_matching_engine.py
```

### 3.2 Core Data Models

#### Document (Base)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| document_type | Enum | INVOICE, PO, GRN |
| document_number | String | External reference |
| supplier_id | UUID | FK to supplier |
| customer_id | UUID | FK to customer |
| issue_date | Date | |
| total_amount | Decimal(12,4) | |
| currency | String(3) | ISO 4217 |
| lines | List[LineItem] | |
| metadata | JSON | Raw extra fields |

#### LineItem
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| line_number | Integer | |
| product_code | String | SKU/EAN |
| description | String | |
| quantity | Decimal(12,4) | |
| unit_price | Decimal(12,4) | |
| total_price | Decimal(12,4) | |
| tax_rate | Decimal(5,4) | |

#### MatchResult
| Field | Type | Notes |
|-------|------|-------|
| status | Enum | MATCHED, MISMATCHED, PARTIAL, PENDING_REVIEW |
| match_score | Decimal(5,2) | 0.00–100.00 |
| invoice_id | UUID | |
| po_id | UUID | |
| grn_id | UUID | |
| line_results | List[LineMatchResult] | |
| mismatch_reasons | List[MismatchReason] | |
| matched_at | DateTime | |
| confidence_level | Enum | HIGH, MEDIUM, LOW |

#### MismatchReason
| Field | Type | Notes |
|-------|------|-------|
| field | String | e.g., "total_amount" |
| expected | Any | |
| actual | Any | |
| tolerance | Decimal | |
| severity | Enum | BLOCKING, WARNING, INFO |

---

## 4. Matching Algorithm

### 4.1 Three-Way Match Rules

**Rule Set 1: Exact Match Criteria (all must pass)**
- [ ] Invoice supplier_id == PO supplier_id
- [ ] Invoice customer_id == PO customer_id
- [ ] Invoice currency == PO currency
- [ ] Invoice issue_date <= PO delivery_date + 90 days

**Rule Set 2: Amount Validation**
- [ ] Invoice total (ex-tax) within ±X% of PO total (ex-tax), configurable tolerance (default: 0.01%)
- [ ] Invoice tax amount matches line-level tax computation
- [ ] Per-line: line total within ±tolerance of PO line total

**Rule Set 3: Quantity Validation**
- [ ] Sum of GRN quantities per line >= PO quantity (allowing partial delivery)
- [ ] Invoice quantity <= GRN quantity (invoice cannot exceed delivered)
- [ ] Configurable under-delivery tolerance (default: 2%)

**Rule Set 4: Line-Level Matching**
- [ ] Product code match (exact EAN/SKU match preferred)
- [ ] Fallback: fuzzy description match with Levenshtein threshold
- [ ] Line-level match score aggregated to document-level

### 4.2 Matching Flow

```
1. RECEIVE (invoice_id, po_id, grn_id)
       │
2. VALIDATE_DOCUMENTS
       │ ── Validate each document exists and is valid
       │ ── Extract and normalize fields
       ▼
3. CHECK_RULE_SET_1 (Basic validation)
       │ ── Pass → Continue
       │ ── Fail → Return MISMATCHED with BLOCKING reasons
       ▼
4. CHECK_RULE_SET_2 (Amount validation)
       │ ── Pass → Continue
       │ ── Fail → Mark as PENDING_REVIEW or MISMATCHED
       ▼
5. CHECK_RULE_SET_3 (Quantity via GRN)
       │ ── Pass → Continue
       │ ── Fail → Mark as PARTIAL or PENDING_REVIEW
       ▼
6. LINE_LEVEL_MATCH
       │ ── For each invoice line:
       │    a. Find corresponding PO line (by product code)
       │    b. Find corresponding GRN line(s)
       │    c. Compute line match score
       ▼
7. AGGREGATE_SCORE
       │ ── Weighted average of line scores
       │ ── Apply threshold (default: 95%)
       ▼
8. RETURN MatchResult
```

### 4.3 Tolerance Configuration (config.yaml)

```yaml
matching:
  tolerances:
    amount_percent: 0.01      # 0.01% = exact match
    amount_absolute: 0.01    # EUR fallback
    quantity_percent: 2.0    # Under-delivery tolerance
    date_days: 90             # Max days between invoice and PO
  scoring:
    line_weight: 0.7         # Line-level weight
    amount_weight: 0.2       # Amount match weight
    date_weight: 0.1         # Date sequence weight
  thresholds:
    match: 95.0              # Minimum score for MATCHED
    partial: 70.0            # Minimum score for PARTIAL
    review: 50.0             # Minimum score for PENDING_REVIEW
```

---

## 5. Functionality Specification

### 5.1 Core Features

| # | Feature | Description | Priority |
|---|---------|-------------|----------|
| F1 | Document Ingestion | Accept normalized Invoice, PO, GRN objects | MUST |
| F2 | Field Normalization | Standardize dates, amounts, product codes | MUST |
| F3 | Rule Set 1 Validation | Basic document consistency checks | MUST |
| F4 | Amount Matching | Total and line-level amount comparison with tolerance | MUST |
| F5 | Quantity Matching | PO vs GRN vs Invoice quantity chain | MUST |
| F6 | Line-Level Matching | Per-line product code and description matching | MUST |
| F7 | Score Aggregation | Weighted document-level match score | MUST |
| F8 | Mismatch Explanation | Human-readable mismatch reasons | MUST |
| F9 | Configurable Tolerances | YAML-driven tolerance configuration | SHOULD |
| F10 | Partial Match Handling | Support partial deliveries | SHOULD |
| F11 | Fuzzy Product Matching | Levenshtein-based description matching | COULD |

### 5.2 API Interface

```python
from src.core.engine import MatchingEngine
from src.core.models import MatchResult

engine = MatchingEngine(config_path="config.yaml")

result: MatchResult = engine.match(
    invoice_id="uuid-invoice",
    po_id="uuid-po", 
    grn_id="uuid-grn"
)

# Result inspection
assert result.status in ["MATCHED", "MISMATCHED", "PARTIAL", "PENDING_REVIEW"]
print(f"Score: {result.match_score}%")
for reason in result.mismatch_reasons:
    print(f"  [{reason.severity}] {reason.field}: expected {reason.expected}, got {reason.actual}")
```

### 5.3 Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Invoice before PO | BLOCKING — invoice cannot precede PO |
| Invoice quantity > GRN quantity | BLOCKING — cannot invoice undelivered |
| GRN quantity > PO quantity | WARNING — possible over-delivery |
| Missing product code | Fallback to description matching |
| Currency mismatch | BLOCKING — currency must match |
| Supplier mismatch | BLOCKING — invoice supplier ≠ PO supplier |
| Zero-value lines | Handle division-by-zero in ratio calculations |
| Missing GRN | Allow 2-way match (Invoice vs PO) with flag |

---

## 6. Acceptance Criteria

### 6.1 Functional Criteria

- [ ] `MatchingEngine.match(invoice_id, po_id, grn_id)` returns `MatchResult`
- [ ] Exact match (all values within tolerance) returns status=MATCHED, score=100.0
- [ ] Supplier mismatch returns MISMATCHED with BLOCKING reason
- [ ] Amount > tolerance returns PENDING_REVIEW or MISMATCHED based on threshold
- [ ] Partial delivery (GRN < PO) returns PARTIAL status
- [ ] All mismatch reasons are captured with field, expected, actual, severity
- [ ] Line-level results are included in MatchResult.line_results

### 6.2 Technical Criteria

- [ ] All tolerances configurable via `config.yaml` without code changes
- [ ] No hardcoded magic numbers for tolerances
- [ ] Decimal precision maintained throughout (no floating-point errors)
- [ ] UUID-based primary keys on all entities
- [ ] Timestamps (created_at, updated_at) on all entities
- [ ] Unit test coverage ≥ 80% for core matching logic

### 6.3 Performance Criteria

- [ ] Single match operation completes in < 50ms for typical 20-line documents
- [ ] Engine can process 100 concurrent match requests without degradation

---

## 7. Dependencies

```txt
# requirements.txt (Phase 3 only)
pydantic>=2.0
PyYAML>=6.0
python-dateutil>=2.8
rapidfuzz>=3.0  # For fuzzy string matching (optional)
pytest>=7.4
pytest-cov>=4.1
```

---

## 8. Out of Scope (Phase 3)

- Database persistence (handled in Phase 4)
- REST API endpoints (handled in Phase 4)
- Learning loop / ML components (Phase 5+)
- Authentication / Authorization
- Multi-currency conversion
- EDI parsing (Invoice, PO, GRN are pre-normalized inputs)

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Match correctness | 100% on golden dataset |
| False positive rate | < 0.1% |
| Processing time (p50) | < 20ms |
| Unit test coverage | ≥ 80% |
| Configuration coverage | 100% of tolerances externalized |

---

## 10. Files to Create

The following files must be created in Phase 3:

### Core Module
```
src/core/__init__.py
src/core/engine.py
src/core/config.py
```

### Matchers
```
src/core/matchers/__init__.py
src/core/matchers/invoice.py
src/core/matchers/po.py
src/core/matchers/grn.py
src/core/matchers/line.py
```

### Validators
```
src/core/validators/__init__.py
src/core/validators/amount.py
src/core/validators/date.py
src/core/validators/quantity.py
src/core/validators/currency.py
```

### Models
```
src/core/models/__init__.py
src/core/models/document.py
src/core/models/line.py
src/core/models/match_result.py
src/core/models/mismatch.py
```

### Tests
```
src/tests/unit/test_matching_engine.py
```

### Configuration
```
config.yaml
```

### Requirements
```
requirements.txt (Phase 3 dependencies)
```

---

## 11. Next Phase

Phase 4: API Platform — Expose matching engine via FastAPI REST endpoints with PostgreSQL persistence.
