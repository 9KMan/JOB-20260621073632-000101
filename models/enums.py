# models/enums.py
"""Enumeration types for AP Automation Engine."""

from enum import StrEnum


class InvoiceStatus(StrEnum):
    """Invoice status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class InvoiceType(StrEnum):
    """Invoice type enumeration."""

    STANDARD = "standard"
    CREDIT_MEMO = "credit_memo"
    DEBIT_MEMO = "debit_memo"
    SELF_INVOICE = "self_invoice"


class POStatus(StrEnum):
    """Purchase order status enumeration."""

    DRAFT = "draft"
    OPEN = "open"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class POType(StrEnum):
    """Purchase order type enumeration."""

    STANDARD = "standard"
    BLANKET = "blanket"
    CONTRACT = "contract"


class DeliveryNoteStatus(StrEnum):
    """Delivery note status enumeration."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class MatchStatus(StrEnum):
    """Match status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AUTO_MATCHED = "auto_matched"
    EXCEPTION = "exception"
    DISMISSED = "dismissed"


class DecisionType(StrEnum):
    """Match decision type enumeration."""

    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    DISMISS = "dismiss"
    ANCHOR = "anchor"
    PARTIAL = "partial"


class ExceptionType(StrEnum):
    """Exception type enumeration."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OVERDELIVERY = "overdelivery"
    UNDERDELIVERY = "underdelivery"
    NO_MATCH_FOUND = "no_match_found"
    MULTIPLE_MATCHES = "multiple_matches"
    BLOCKED = "blocked"


class ExceptionStatus(StrEnum):
    """Exception status enumeration."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
