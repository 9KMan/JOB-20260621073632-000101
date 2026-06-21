# models/enums.py
"""SQLAlchemy and Pydantic enum definitions."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Status of an invoice."""

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
    """Status of a purchase order."""

    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Status of a delivery note."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    FULLY_INVOICED = "fully_invoiced"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    """Status of a matching process."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchDecision(str, Enum):
    """Decision outcome of the matching engine."""

    AUTO_APPROVED = "auto_approved"
    REVIEW_REQUIRED = "review_required"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class MatchConfidence(str, Enum):
    """Confidence level of a match."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionReason(str, Enum):
    """Reason for an exception."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    NO_PO_FOUND = "no_po_found"
    PARTIAL_MATCH = "partial_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_MISMATCH = "date_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"
    OTHER = "other"


class ExceptionStatus(str, Enum):
    """Status of an exception."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
