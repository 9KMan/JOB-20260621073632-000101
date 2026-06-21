# models/enums.py
"""Enumeration types for the AP Automation Engine.

Defines all status enums, decision types, and other categorical values
used throughout the application.
"""

import enum


class InvoiceStatus(str, enum.Enum):
    """Invoice processing status."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class MatchingDecision(str, enum.Enum):
    """Matching engine decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


class MatchConfidence(str, enum.Enum):
    """Confidence level of a match."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class LineMatchStatus(str, enum.Enum):
    """Status of a line-level match."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL = "partial"
    OVERDELIVERED = "overdelivered"
    UNDERDELIVERED = "underdelivered"
    NO_MATCH = "no_match"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    TAX_VARIANCE = "tax_variance"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_MATCHES = "multiple_matches"
    BLIND_MATCH = "blind_match"


class ExceptionResolution(str, enum.Enum):
    """How an exception was resolved."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class BalanceType(str, enum.Enum):
    """Type of balance entry."""

    ORIGINAL = "original"
    INVOICE = "invoice"
    DELIVERY = "delivery"
    CREDIT = "credit"
    ADJUSTMENT = "adjustment"


class LearningStatus(str, enum.Enum):
    """Status of a cross-reference learning entry."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
