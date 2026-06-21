# models/enums.py
"""Status enums and decision types for the AP Automation Engine."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING_IN_PROGRESS = "matching_in_progress"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(str, enum.Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Status values for match attempts."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Decision outcomes from the matching engine."""

    AUTO_APPROVED = "auto_approved"
    REVIEW_REQUIRED = "review_required"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"
    MANUAL_REVIEW = "manual_review"


class ExceptionStatus(str, enum.Enum):
    """Status values for matching exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_PO_MATCH = "multiple_po_match"
    UNMATCHED_LINES = "unmatched_lines"
    DELIVERY_DATE_MISMATCH = "delivery_date_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"


class MatchConfidence(str, enum.Enum):
    """Confidence levels for match scores."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class MatchLayer(str, enum.Enum):
    """Matching engine layers."""

    ANCHORING = "anchoring"
    CASCADE = "cascade"
    BALANCES = "balances"
    SCORING = "scoring"
    LEARNING = "learning"
