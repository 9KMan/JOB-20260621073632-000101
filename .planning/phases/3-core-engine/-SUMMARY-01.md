# Phase 3 Summary — Core Matching Engine
## Finaro AP Automation

---

## Phase 3 Overview

**Status:** READY FOR IMPLEMENTATION  
**Priority:** CRITICAL  
**Duration:** 40–60 hours (of 150–225 total budget)

---

## What This Phase Delivers

### Core Deliverable
A deterministic Python matching engine that performs 3-way matching of:
- **Supplier Invoices** 
- **Purchase Orders (POs)**
- **Delivery Notes (GRNs/Albaranes)**

### Key Features
1. **Rule-Based Matching** — Four rule sets covering document validation, amount, quantity, and line-level matching
2. **Configurable Tolerances** — All matching thresholds externalized to YAML configuration
3. **Match Scoring** — Weighted scoring algorithm (line-level 70%, amount 20%, date 10%)
4. **Mismatch Explanation** — Human-readable BLOCKING/WARNING/INFO reasons for non-matches
5. **Partial Delivery Support** — Handles under-delivery scenarios with configurable tolerance

---

## Architecture Decisions

### Module Location
```
src/core/
├── engine.py           # Main orchestrator
├── matchers/          # Document-specific matching logic
├── validators/        # Amount, date, quantity, currency validation
├── models/            # Pydantic data models
└── config.py          # Configuration management
```

### Key Design Choices
| Decision | Rationale |
|----------|-----------|
| Pydantic models | Type safety, validation, serialization |
| UUID primary keys | No information leakage, distributed-system friendly |
| Decimal(12,4) | Financial precision, no floating-point errors |
| YAML configuration | Business users can adjust tolerances without code |
| Weighted scoring | Provides nuanced match quality beyond boolean |

---

## Acceptance Criteria Checklist

- [ ] MatchingEngine.match() returns MatchResult with status, score, reasons
- [ ] Exact match → MATCHED (100%)
- [ ] Supplier/currency mismatch → MISMATCHED (BLOCKING)
- [ ] Amount tolerance breach → PENDING_REVIEW or MISMATCHED
- [ ] Partial delivery → PARTIAL with line-level detail
- [ ] 80%+ unit test coverage on core logic
- [ ] All tolerances configurable without code changes

---

## Dependencies Added

```
pydantic>=2.0
PyYAML>=6.0
python-dateutil>=2.8
pytest>=7.4
pytest-cov>=4.1
```

---

## What Is NOT In Scope

- Database persistence (Phase 4)
- REST API endpoints (Phase 4)
- Authentication/authorization (Phase 4)
- ML learning loop (Phase 5+)
- Multi-currency conversion
- EDI document parsing

---

## Success Gate

Phase 4 (API Platform) cannot begin until Phase 3:
- Passes all unit tests
- Achieves ≥ 80% code coverage
- Passes golden dataset validation
- Documents all configuration options

---

## Files to Create

```
src/core/__init__.py
src/core/engine.py
src/core/config.py
src/core/matchers/__init__.py
src/core/matchers/invoice.py
src/core/matchers/po.py
src/core/matchers/grn.py
src/core/matchers/line.py
src/core/validators/__init__.py
src/core/validators/amount.py
src/core/validators/date.py
src/core/validators/quantity.py
src/core/validators/currency.py
src/core/models/__init__.py
src/core/models/document.py
src/core/models/line.py
src/core/models/match_result.py
src/core/models/mismatch.py
config.yaml
requirements.txt
tests/unit/test_matching_engine.py
tests/unit/test_validators.py
tests/unit/test_matchers.py
```
