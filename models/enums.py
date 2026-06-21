# models/enums.py
"""Status enums and decision types for AP Automation Engine."""

from enum import StrEnum


class InvoiceStatus(StrEnum):
    """Status values for invoices."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    MATCHING = "MATCHING"
    MATCHED = "MATCHED"
    APPROVED = "APPROVED"
    EXCEPTION = "EXCEPTION"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PurchaseOrderStatus(StrEnum):
    """Status values for purchase orders."""

    DRAFT = "DRAFT"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class DeliveryNoteStatus(StrEnum):
    """Status values for delivery notes."""

    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    RECEIVED = "RECEIVED"
    PARTIALLY_INVOICED = "PARTIALLY_INVOICED"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"


class LineStatus(StrEnum):
    """Status values for document lines."""

    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    CANCELLED = "CANCELLED"


class MatchingStatus(StrEnum):
    """Status values for matching operations."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NO_MATCH = "NO_MATCH"


class DecisionType(StrEnum):
    """Decision types for matching results."""

    AUTO_APPROVED = "AUTO_APPROVED"
    REVIEW = "REVIEW"
    EXCEPTION = "EXCEPTION"
    REJECTED = "REJECTED"


class ExceptionReason(StrEnum):
    """Reasons for exceptions in matching."""

    PRICE_MISMATCH = "PRICE_MISMATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    MISSING_PO = "MISSING_PO"
    MISSING_DELIVERY_NOTE = "MISSING_DELIVERY_NOTE"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    CROSS_COMPANY = "CROSS_COMPANY"
    DUPLICATE_MATCH = "DUPLICATE_MATCH"
    EXCEEDS_PO_AMOUNT = "EXCEEDS_PO_AMOUNT"
    UNMATCHED_LINES = "UNMATCHED_LINES"


class ExceptionStatus(StrEnum):
    """Status values for exceptions."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    ESCALATED = "ESCALATED"
