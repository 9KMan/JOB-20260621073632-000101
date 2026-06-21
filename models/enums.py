// models/enums.py
"""Enumeration types for the AP Automation Engine."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    RECEIVED = "received"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class LineStatus(str, enum.Enum):
    """Status values for invoice/PO lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Status values for match records."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXCEPTION = "exception"


class DecisionType(str, enum.Enum):
    """Decision types from the matching engine."""

    AUTO_APPROVE = "auto_approve"
    REVIEW = "review"
    EXCEPTION = "exception"
    REJECT = "reject"


class MatchConfidence(str, enum.Enum):
    """Confidence levels for matches."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class ExceptionType(str, enum.Enum):
    """Types of exceptions that can occur."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    NO_MATCH = "no_match"


class ExceptionResolution(str, enum.Enum):
    """Ways to resolve an exception."""

    APPROVED = "approved"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    ADJUSTED = "adjusted"
    ESCALATED = "escalated"
