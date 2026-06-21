# models/enums.py
"""SQLAlchemy-compatible and Pydantic enum definitions."""

import enum


# ── Invoice ───────────────────────────────────────────────────────────────────

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHING = "matching"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"


# ── Purchase Order ─────────────────────────────────────────────────────────────

class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# ── Delivery Note ─────────────────────────────────────────────────────────────

class DeliveryNoteStatus(str, enum.Enum):
    RECEIVED = "received"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


# ── Matching ──────────────────────────────────────────────────────────────────

class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_CANDIDATES = "no_candidates"


class LineMatchStatus(str, enum.Enum):
    UNMATCHED = "unmatched"
    MATCHED = "matched"
    PARTIAL = "partial"
    OVER_DELIVERED = "over_delivered"


class MatchConfidence(str, enum.Enum):
    """Confidence level derived from the match score."""
    HIGH = "high"      # >= THRESHOLD_HIGH
    MEDIUM = "medium"  # >= THRESHOLD_MID
    LOW = "low"        # >= THRESHOLD_LOW
    EXCEPTION = "exception"  # below threshold_low


# ── Approval Decision ─────────────────────────────────────────────────────────

class ApprovalDecision(str, enum.Enum):
    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"


# ── Exceptions ────────────────────────────────────────────────────────────────

class ExceptionStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, enum.Enum):
    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MULTIPLE_PO_CANDIDATES = "multiple_po_candidates"
    NO_LINE_MATCH = "no_line_match"
    PARTIAL_LINE_MATCH = "partial_line_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OTHER = "other"
