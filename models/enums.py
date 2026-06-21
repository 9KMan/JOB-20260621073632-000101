# models/enums.py
"""Enumeration types for the AP Automation Engine."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status values."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    MATCHING = "MATCHING"
    MATCHED = "MATCHED"
    APPROVED = "APPROVED"
    REVIEW = "REVIEW"
    EXCEPTION = "EXCEPTION"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status values."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status values."""

    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    RECEIVED = "RECEIVED"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"


class MatchDecision(str, Enum):
    """Matching decision outcomes."""

    APPROVED = "APPROVED"
    REVIEW = "REVIEW"
    EXCEPTION = "EXCEPTION"
    REJECTED = "REJECTED"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "PRICE_VARIANCE"
    QUANTITY_VARIANCE = "QUANTITY_VARIANCE"
    MISSING_PO = "MISSING_PO"
    MISSING_INVOICE = "MISSING_INVOICE"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    DUPLICATE_PO = "DUPLICATE_PO"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    OVER_DELIVERY = "OVER_DELIVERY"
    UNDER_DELIVERY = "UNDER_DELIVERY"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    DATE_VARIANCE = "DATE_VARIANCE"
    VENDOR_MISMATCH = "VENDOR_MISMATCH"
    UNEXPECTED_CHARGE = "UNEXPECTED_CHARGE"
    OTHER = "OTHER"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    ESCALATED = "ESCALATED"


class MatchConfidence(str, Enum):
    """Match confidence levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class LearningStatus(str, Enum):
    """Cross-reference learning status."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PROMOTED = "PROMOTED"
    DEMOTED = "DEMOTED"
    ARCHIVED = "ARCHIVED"
