# models/enums.py
"""Status enums and decision types for AP Automation."""

from enum import Enum


class InvoiceStatus(str, Enum):
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


class PurchaseOrderStatus(str, Enum):
    """Purchase order status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching engine decision."""

    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_MATCHES = "multiple_matches"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OVERDELIVERY = "overdelivery"
    PARTIAL_DELIVERY = "partial_delivery"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineStatus(str, Enum):
    """Status for individual invoice/PO/DN lines."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
