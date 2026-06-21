# models/enums.py
"""Enum definitions for AP Automation Engine.

Defines status enums, decision types, and other enumerated values
used throughout the application.
"""

import enum


class InvoiceStatus(str, enum.Enum):
    """Status values for Invoice records."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status values for Purchase Order records."""

    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Status values for Delivery Note records."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_PROCESSED = "partially_processed"
    PROCESSED = "processed"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Matching engine decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"
    MANUAL_REVIEW = "manual_review"


class MatchConfidence(str, enum.Enum):
    """Confidence level for match decisions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, enum.Enum):
    """Types of exceptions in the matching process."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_INVOICE = "missing_invoice"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DUPLICATE_PO = "duplicate_po"
    DATE_VARIANCE = "date_variance"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    MULTIPLE_MATCHES = "multiple_matches"
    ORPHANED_LINES = "orphaned_lines"
    OTHER = "other"


class ExceptionStatus(str, enum.Enum):
    """Status of exception records."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineStatus(str, enum.Enum):
    """Status for individual line items."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"
    CANCELLED = "cancelled"


class LedgerEntryType(str, enum.Enum):
    """Types of entries in the balance ledger."""

    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    CREDIT_NOTE = "credit_note"
    MANUAL_ADJUSTMENT = "manual_adjustment"
