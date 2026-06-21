# models/enums.py
"""Enumerations for AP Automation Engine models."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status values."""

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
    """Purchase order status values."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status values."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching decision types."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class ExceptionType(str, Enum):
    """Exception types in matching."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DUPLICATE_PAYMENT = "duplicate_payment"
    UNMATCHED_LINES = "unmatched_lines"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    DUPLICATE_PO = "duplicate_po"
    EXPIRED_PO = "expired_po"
    CANCELLED_PO = "cancelled_po"
    CLOSED_PO = "closed_po"


class ExceptionStatus(str, Enum):
    """Exception status values."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class LedgerTransactionType(str, Enum):
    """Balance ledger transaction types."""

    INVOICE = "invoice"
    PAYMENT = "payment"
    CREDIT_MEMO = "credit_memo"
    ADJUSTMENT = "adjustment"
    WRITE_OFF = "write_off"


class MatchSource(str, Enum):
    """Source of match confirmation for learning."""

    MANUAL = "manual"
    AUTO_APPROVED = "auto_approved"
    USER_CONFIRMATION = "user_confirmation"
    LEARNING_PROMOTED = "learning_promoted"


__all__ = [
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchDecision",
    "ExceptionType",
    "ExceptionStatus",
    "MatchConfidence",
    "LedgerTransactionType",
    "MatchSource",
]
