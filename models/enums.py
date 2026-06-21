# models/enums.py
"""Status enums and decision types for the matching engine."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Invoice processing status."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Matching decision outcome."""

    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class MatchConfidence(str, enum.Enum):
    """Match confidence level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    OVER_INVOICED = "over_invoiced"
    UNDER_INVOICED = "under_invoiced"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"


class ExceptionStatus(str, enum.Enum):
    """Exception resolution status."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
