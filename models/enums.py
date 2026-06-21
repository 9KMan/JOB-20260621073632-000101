# models/enums.py
"""Enumeration types for the application."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    OPEN = "open"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    PENDING = "pending"


class MatchStatus(str, Enum):
    """Status values for match records."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class LineType(str, Enum):
    """Types of line items."""

    STANDARD = "standard"
    MISC = "misc"
    SERVICE = "service"
    TAX = "tax"
    FREIGHT = "freight"


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    JPY = "JPY"
