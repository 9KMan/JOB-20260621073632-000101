# Phase 6 — Learning Loop
## FinaRo AP Automation Core Engine

---

## 1. Phase Overview

**Phase:** 6 of 7
**Subject:** Learning Loop — `cross_ref` Persistence and Adaptive Matching
**Goal:** Implement the self-improving matching mechanism that stores human confirmations and promotes future matches to high-confidence (Level 1), making FinaRo's engine smarter over time.

---

## 2. What Is the Learning Loop?

The learning loop is FinaRo's **defensible IP** — the mechanism that turns a human review action into an automated future decision.

Every time a matcher presents a mid-confidence candidate and a user confirms the correct pairing, that confirmation is written to the `cross_ref` table. On the next invoice from the same supplier, the engine promotes that confirmed pair to **Level 1 (highest confidence)**, bypassing all lower-cascade methods.

**Loop diagram:**

```
Invoice line arrives
        │
        ▼
┌───────────────────────┐
│  Try cascade in order  │
│  1. cross_ref (learned)│  ◄── promotes to here after first human confirm
│  2. SKU / EAN          │
│  3. Description fuzzy  │
│  4. Price + quantity   │
└───────────────────────┘
        │
   Human review
   confirms match
        │
        ▼
┌───────────────────────┐
│  Write to cross_ref   │
│  supplier + sku_pair  │
└───────────────────────┘
        │
        ▼
  Next invoice from
  same supplier uses
  Level 1 match ──────► Auto-post
```

---

## 3. Data Model — `cross_ref` Table

### 3.1 Schema

```sql
CREATE TABLE cross_ref (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id     UUID NOT NULL REFERENCES suppliers(id),
    invoice_sku     TEXT NOT NULL,          -- SKU/description as it appears on invoice
    po_sku          TEXT NOT NULL,           -- SKU as it appears on PO
    match_method    TEXT NOT NULL,           -- 'description_fuzzy' | 'price_qty' | 'ean' | 'manual'
    confidence      FLOAT NOT NULL DEFAULT 1.0,  -- 0.0–1.0; 1.0 = human-confirmed
    confirmed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_by    UUID REFERENCES users(id),
    invoice_id      UUID REFERENCES invoices(id),  -- the invoice that triggered confirmation
    po_line_id      UUID REFERENCES po_lines(id),  -- the PO line it was matched to
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cross_ref_supplier ON cross_ref(supplier_id, is_active);
CREATE UNIQUE INDEX idx_cross_ref_invoice_sku ON cross_ref(supplier_id, invoice_sku, is_active) WHERE is_active = TRUE;
```

### 3.2 Unique-Key Strategy

The unique constraint is `(supplier_id, invoice_sku, is_active=TRUE)`. When a better match is confirmed, the old row is soft-deleted (`is_active=FALSE`) and a new row is written. This preserves history without losing the audit trail.

---

## 4. Learning Loop API — Service Layer

### 4.1 `LearningService` class

**File:** `src/services/learning_service.py`

```python
class LearningService:
    """Manages the cross_ref learning loop — write confirmations and query promoted matches."""

    def confirm_match(
        self,
        supplier_id: UUID,
        invoice_sku: str,
        po_sku: str,
        match_method: str,        # the cascade level that was overridden
        confirmed_by: UUID,
        invoice_id: UUID,
        po_line_id: UUID,
    ) -> CrossRef:
        """
        Called when a human confirms a match at a lower cascade level.
        Writes a new cross_ref entry (or re-activates an existing one).
        """

    def get_promoted_match(
        self,
        supplier_id: UUID,
        invoice_sku: str,
    ) -> CrossRef | None:
        """
        Called at the START of the cascade (before any other matching).
        Returns a cross_ref entry if one exists for (supplier, invoice_sku).
        This promotes it to Level 1 — the highest confidence path.
        """

    def deactivate_outdated(
        self,
        supplier_id: UUID,
        invoice_sku: str,
    ) -> int:
        """
        Called before writing a new confirmed entry.
        Soft-deletes (is_active=FALSE) any existing entry for (supplier, invoice_sku).
        Returns count of rows deactivated.
        """
```

---

## 5. Integration into Matching Cascade

### 5.1 Modified `MatchingService.cascade_match()`

The matching cascade in `src/services/matching_service.py` is updated as follows:

```python
def cascade_match(self, invoice_line: InvoiceLine, candidate_pos: list[POLine]) -> MatchResult:
    supplier_id = invoice_line.supplier_id

    # ── LEVEL 0: Learned (promoted from cross_ref) ──────────────────
    promoted = self.learning_service.get_promoted_match(supplier_id, invoice_line.sku)
    if promoted:
        return MatchResult(
            level=0,
            method="cross_ref_promoted",
            confidence=1.0,
            po_line_id=promoted.po_line_id,
            cross_ref_id=promoted.id,
        )

    # ── LEVEL 1: SKU / EAN / barcode ────────────────────────────────
    # ... (existing high-confidence matching)

    # ── LEVEL 2: Description fuzzy + price proximity ─────────────
    # ... (existing mid-confidence matching)

    # ── LEVEL 3: Price + quantity ─────────────────────────────────
    # ... (existing low-confidence matching)

    # ── NO MATCH: return unmatched ─────────────────────────────────
    return MatchResult(level=None, method=None, confidence=0.0, po_line_id=None)
```

**Key rule:** `get_promoted_match()` is called before all other cascade levels. If it returns a result, the cascade **stops** there — no lower levels are tried.

### 5.2 Confirmation Handler — `confirm_match()`

After a human confirms a mid/low match in the UI:

1. Call `learning_service.confirm_match(...)` with all context
2. The service writes the `cross_ref` row
3. The next invoice from the same supplier automatically uses Level 0

### 5.3 Score Influence

Confirmed matches contribute to the overall invoice score:

| Scenario | Score contribution |
|---|---|
| All lines matched at Level 0 (cross_ref) | Full auto-post weight |
| Some lines confirmed by human | Mid-band → 1-click review |
| No match found for any line | Exception threshold |

---

## 6. API Endpoints

### 6.1 `POST /api/v1/learning/confirm`

Called by the review UI when a human confirms a match.

**Request:**
```json
{
  "invoice_id": "uuid",
  "invoice_line_id": "uuid",
  "po_line_id": "uuid",
  "match_method": "description_fuzzy",
  "confirmed_by": "uuid",
  "invoice_sku": "string",
  "po_sku": "string"
}
```

**Response:** `201 Created`
```json
{
  "cross_ref_id": "uuid",
  "supplier_id": "uuid",
  "invoice_sku": "string",
  "confidence": 1.0,
  "confirmed_at": "2026-06-21T10:00:00Z"
}
```

### 6.2 `GET /api/v1/learning/promoted/{supplier_id}/{invoice_sku}`

Debug/audit endpoint — returns the current promoted match for a supplier+sku pair.

**Response:** `200 OK` or `404 Not Found`

### 6.3 `GET /api/v1/learning/supplier/{supplier_id}`

List all active `cross_ref` entries for a supplier (for the review UI).

**Response:** `200 OK`
```json
{
  "supplier_id": "uuid",
  "entries": [
    {
      "id": "uuid",
      "invoice_sku": "string",
      "po_sku": "string",
      "match_method": "description_fuzzy",
      "confidence": 1.0,
      "confirmed_at": "2026-06-21T10:00:00Z",
      "invoice_id": "uuid"
    }
  ]
}
```

### 6.4 `DELETE /api/v1/learning/{cross_ref_id}`

Soft-delete a cross_ref entry (admin/override).

**Response:** `204 No Content`

---

## 7. Database Migration

**File:** `migrations/versions/006_add_cross_ref.py`

```python
"""Add cross_ref table for learning loop."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

op.create_table(
    "cross_ref",
    sa.Column("id", UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
    sa.Column("supplier_id", UUID(), nullable=False),
    sa.Column("invoice_sku", sa.Text(), nullable=False),
    sa.Column("po_sku", sa.Text(), nullable=False),
    sa.Column("match_method", sa.Text(), nullable=False),
    sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
    sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    sa.Column("confirmed_by", UUID(), nullable=True),
    sa.Column("invoice_id", UUID(), nullable=True),
    sa.Column("po_line_id", UUID(), nullable=True),
    sa.Column("is_active", sa.Boolean(), nullable=False, server_default="TRUE"),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    sa.PrimaryKeyConstraint("id"),
)
op.create_index("idx_cross_ref_supplier", "cross_ref", ["supplier_id", "is_active"])
op.create_index(
    "idx_cross_ref_invoice_sku_unique",
    "cross_ref",
    ["supplier_id", "invoice_sku"],
    unique=True,
    postgresql_where=sa.text("is_active = TRUE"),
)
op.create_foreign_key("fk_cross_ref_supplier", "cross_ref", "suppliers", ["supplier_id"], ["id"])
op.create_foreign_key("fk_cross_ref_confirmed_by", "cross_ref", "users", ["confirmed_by"], ["id"])
op.create_foreign_key("fk_cross_ref_invoice", "cross_ref", "invoices", ["invoice_id"], ["id"])
op.create_foreign_key("fk_cross_ref_po_line", "cross_ref", "po_lines", ["po_line_id"], ["id"])
```

---

## 8. Testing

### 8.1 Unit Tests — `tests/test_learning_service.py`

```python
class TestLearningService:
    def test_confirm_match_writes_cross_ref_row(self, ...): ...
    def test_confirm_match_soft_deletes_previous_active(self, ...): ...
    def test_get_promoted_match_returns_active_entry(self, ...): ...
    def test_get_promoted_match_returns_none_when_no_entry(self, ...): ...
    def test_deactivate_outdated_sets_is_active_false(self, ...): ...
```

### 8.2 Integration Tests — `tests/test_learning_loop_integration.py`

```python
class TestLearningLoopIntegration:
    def test_human_confirm_next_invoice_uses_promoted_match(self, ...):
        """
        Scenario:
        1. Invoice A arrives — description fuzzy match used (mid confidence)
        2. Human confirms the match
        3. Invoice B arrives — same supplier, same sku
        4. Engine uses Level 0 (cross_ref_promoted), not cascade
        5. Invoice B auto-posts (no human review needed)
        """
        ...

    def test_confirmed_match_updates_invoice_score(self, ...): ...
    def test_inactive_cross_ref_not_used_for_promotion(self, ...): ...
```

### 8.3 Cascade Integration Test — `tests/test_matching_cascade.py`

```python
class TestCascadeWithLearning:
    def test_cascade_checks_cross_ref_before_all_other_levels(self, ...): ...
    def test_cascade_returns_cross_ref_result_stops_cascade(self, ...): ...
    def test_no_cross_ref_falls_through_to_level_1(self, ...): ...
```

---

## 9. Configuration

| Config key | Default | Description |
|---|---|---|
| `LEARNING_LOOP_ENABLED` | `True` | Master switch for the learning loop |
| `CROSS_REF_CONFIDENCE_BOOST` | `1.0` | Confidence score assigned to confirmed matches |
| `MAX_CROSS_REF_PER_SUPPLIER` | `10000` | Cap to prevent unbounded table growth |

---

## 10. Acceptance Criteria

- [ ] **LL-01**: `cross_ref` table created with correct schema and indexes
- [ ] **LL-02**: `LearningService.confirm_match()` writes a new `cross_ref` row with `confidence=1.0`
- [ ] **LL-03**: `LearningService.get_promoted_match()` returns the correct entry before any cascade lookup
- [ ] **LL-04**: Matching cascade calls `get_promoted_match()` at Level 0 and stops if a match is found
- [ ] **LL-05**: `POST /api/v1/learning/confirm` endpoint accepts valid payload and returns `201`
- [ ] **LL-06**: `GET /api/v1/learning/supplier/{id}` returns all active `cross_ref` entries
- [ ] **LL-07**: When a new confirmation is written, any previous active entry for the same (supplier, sku) is soft-deleted
- [ ] **LL-08**: All `LearningService` methods have unit tests with ≥ 90% branch coverage
- [ ] **LL-09**: End-to-end integration test confirms: human confirm → next invoice auto-posts
- [ ] **LL-10**: Migration `006_add_cross_ref.py` runs without errors against a fresh database

---

## 11. Phase 6 Deliverables

1. `6-learning-loop/PLAN-01.md` — this document
2. `6-learning-loop/-SUMMARY-01.md` — condensed executive summary
3. `src/services/learning_service.py` — `LearningService` class
4. `src/models/cross_ref.py` — SQLAlchemy model
5. `src/schemas/learning.py` — Pydantic schemas for API
6. `src/api/routes/learning.py` — REST endpoints
7. `migrations/versions/006_add_cross_ref.py` — Alembic migration
8. `tests/test_learning_service.py` — unit tests
9. `tests/test_learning_loop_integration.py` — integration tests
10. `tests/test_matching_cascade.py` — cascade integration tests

---

## 12. Dependencies & Blockers

| Dependency | Blocking | Notes |
|---|---|---|
| Phase 3 — Core Engine (matching cascade) | Yes | Learning loop integrates INTO the cascade; cascade must exist first |
| Phase 5 — Testing & Ops | Partial | Test fixtures from Phase 5 should be reused |
| `suppliers` table | Yes | FK dependency |
| `users` table | No | FK is nullable; existing users table assumed |
| `invoices` / `po_lines` tables | Yes | FK dependencies |
