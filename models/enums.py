# models/enums.py
"""Enumeration types for the AP Automation Engine."""

from enum import Enum


class DocumentStatus(str, Enum):
    """Status values for documents (Invoice, PO, Delivery Note)."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class MatchStatus(str, Enum):
    """Status values for matching operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    NO_MATCH = "no_match"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class DecisionType(str, Enum):
    """Decision types from the matching engine."""

    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECT = "reject"


class ExceptionStatus(str, Enum):
    """Status values for exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, Enum):
    """Reason codes for exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PURCHASE_ORDER = "missing_purchase_order"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    PARTIAL_DELIVERY = "partial_delivery"
    OVERDELIVERY = "overdelivery"
    UNDERDELIVERY = "underdelivery"
    UNMATCHED_LINES = "unmatched_lines"
    PO_EXPIRED = "po_expired"
    PO_CLOSED = "po_closed"
    VENDOR_MISMATCH = "vendor_mismatch"
    DATE_MISMATCH = "date_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    TAX_MISMATCH = "tax_mismatch"
    OTHER = "other"


class LineStatus(str, Enum):
    """Status values for invoice/PO/delivery note lines."""

    OPEN = "open"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
