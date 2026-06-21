// models/enums.py
"""Enumeration types for AP Automation Engine."""

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
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status."""

    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    FULLY_INVOICED = "fully_invoiced"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    """Invoice-PO matching status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    EXCEPTION = "exception"


class DecisionType(str, Enum):
    """Matching decision type."""

    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"


class ExceptionType(str, Enum):
    """Exception categorization types."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    DATE_VARIANCE = "date_variance"
    UNMATCHED_LINE = "unmatched_line"
    MULTIPLE_MATCHES = "multiple_matches"
    CROSS_ENTITY_CONFLICT = "cross_entity_conflict"


class LineStatus(str, Enum):
    """Status for individual invoice/PO/delivery note lines."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class MatchConfidence(str, Enum):
    """Match confidence level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
