// models/enums.py
"""Enum definitions for database models.

This module defines all enumeration types used across the application
for status fields and decision types.
"""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice processing status values."""

    DRAFT = "draft"
    RECEIVED = "received"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class POStatus(str, Enum):
    """Purchase order status values."""

    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status values."""

    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    PARTIALLY_PROCESSED = "partially_processed"
    PROCESSED = "processed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching engine decision types."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    EXCEPTION = "exception"
    PENDING_REVIEW = "pending_review"
    NO_MATCH = "no_match"


class MatchConfidence(str, Enum):
    """Match confidence level indicators."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    DATE_VARIANCE = "date_variance"
    DUPLICATE_MATCH = "duplicate_match"
    UNMATCHED_LINES = "unmatched_lines"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineStatus(str, Enum):
    """Status for invoice/PO/delivery note lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CLOSED = "closed"
    EXCEPTION = "exception"


class MatchType(str, Enum):
    """Types of matches between documents."""

    PO_ANCHORED = "po_anchored"
    DN_ANCHORED = "dn_anchored"
    INVOICE_ONLY = "invoice_only"
    CROSS_REFERENCE = "cross_reference"
    MANUAL = "manual"
