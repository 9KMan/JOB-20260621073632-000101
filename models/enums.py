# models/enums.py
"""Enumeration types for AP Automation Core Engine.

All enums are implemented as Python Enum classes with explicit string values
for database storage and JSON serialization.
"""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status values."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status values."""

    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status values."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    FULLY_INVOICED = "fully_invoiced"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    """Matching status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching decision outcomes.

    HIGH: Auto-approved (above threshold_high)
    MID: 1-click review required (above threshold_mid)
    LOW: Exception flagged (below threshold_low)
    """

    HIGH = "high"
    MID = "mid"
    LOW = "low"
    MANUAL = "manual"
    NO_MATCH = "no_match"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_PO_MATCH = "multiple_po_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    TAX_VARIANCE = "tax_variance"
    CURRENCY_MISMATCH = "currency_mismatch"
    UNKNOWN = "unknown"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, Enum):
    """Match confidence levels based on score."""

    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


__all__ = [
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchStatus",
    "MatchDecision",
    "ExceptionType",
    "ExceptionStatus",
    "MatchConfidence",
]
