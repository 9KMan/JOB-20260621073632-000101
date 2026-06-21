// models/enums.py
"""SQLAlchemy and Pydantic enum definitions for domain status fields."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Lifecycle status of an Invoice record."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHING_IN_PROGRESS = "matching_in_progress"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class POStatus(str, Enum):
    """Lifecycle status of a Purchase Order record."""

    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Lifecycle status of a Delivery Note record."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Outcome of the matching engine for an invoice."""

    AUTO_APPROVED = "auto_approved"   # Score >= threshold_high
    REVIEW_REQUIRED = "review_required"  # threshold_mid <= score < threshold_high
    EXCEPTION = "exception"           # Score < threshold_mid
    PENDING = "pending"               # Not yet processed


class MatchScoreBand(str, Enum):
    """Bucket into which a match score falls for reporting."""

    HIGH = "high"      # >= THRESHOLD_HIGH
    MEDIUM = "medium"  # >= THRESHOLD_MID and < THRESHOLD_HIGH
    LOW = "low"        # < THRESHOLD_MID


class ExceptionType(str, Enum):
    """Classification of a matching exception."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MULTIPLE_PO_MATCHES = "multiple_po_matches"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    UNKNOWN = "unknown"


class ExceptionStatus(str, Enum):
    """Resolution status of a matching exception."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
