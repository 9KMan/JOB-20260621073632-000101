// models/enums.py
"""Enumerations for status fields and decision types."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING_MATCH = "pending_match"
    MATCHED = "matched"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching engine decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MULTIPLE_POS = "multiple_pos"
    DATE_OUT_OF_RANGE = "date_out_of_range"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    AMOUNT_EXCEEDS_PO = "amount_exceeds_po"


class ExceptionStatus(str, Enum):
    """Status of exceptions in the exception queue."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineMatchStatus(str, Enum):
    """Status of individual line matching results."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"
    NO_MATCH = "no_match"


class MatchConfidence(str, Enum):
    """Confidence levels for match decisions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class LearningStatus(str, Enum):
    """Status for learning loop cross-references."""

    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"
