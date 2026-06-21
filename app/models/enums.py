// app/models/enums.py
"""Enum types for the AP Automation system."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice processing status."""

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class POStatus(str, Enum):
    """Purchase order status."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DNStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    RECEIVED = "received"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching engine decision."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    NO_MATCH = "no_match"
    PARTIAL_MATCH = "partial_match"


class MatchConfidence(str, Enum):
    """Match confidence level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DN = "missing_dn"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_CANDIDATE = "no_candidate"
    DATE_MISMATCH = "date_mismatch"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_DELIVERY = "partial_delivery"
    OTHER = "other"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineMatchStatus(str, Enum):
    """Status of line-level matching."""

    PENDING = "pending"
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"


class CrossRefStatus(str, Enum):
    """Cross-reference learning status."""

    PENDING = "pending"
    LEARNING = "learning"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ARCHIVED = "archived"
