// models/enums.py
"""Enum types for the AP Automation Core Engine.

Defines all status enums and decision types used throughout
the application.
"""

from enum import StrEnum


class InvoiceStatus(StrEnum):
    """Invoice status values."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(StrEnum):
    """Purchase order status values."""

    DRAFT = "draft"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(StrEnum):
    """Delivery note status values."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    PARTIAL = "partial"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MatchingStatus(StrEnum):
    """Matching process status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchDecision(StrEnum):
    """Matching decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"
    REJECTED = "rejected"


class ExceptionType(StrEnum):
    """Exception types for matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    TIMING_ISSUE = "timing_issue"
    DUPLICATE_MATCH = "duplicate_match"
    AMOUNT_MISMATCH = "amount_mismatch"
    TAX_VARIANCE = "tax_variance"
    CURRENCY_MISMATCH = "currency_mismatch"


class ExceptionStatus(StrEnum):
    """Exception resolution status values."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineMatchStatus(StrEnum):
    """Line-level matching status."""

    UNMATCHED = "unmatched"
    PARTIAL_MATCH = "partial_match"
    FULL_MATCH = "full_match"
    OVER_MATCH = "over_match"
    CROSS_MATCH = "cross_match"
