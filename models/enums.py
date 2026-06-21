// models/enums.py
"""Enumerations for status fields and decision types."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Match decision outcomes from the matching engine."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    NO_MATCH = "no_match"
    PENDING = "pending"


class MatchStatus(str, Enum):
    """Status values for match records."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    SUPERSEDED = "superseded"


class ExceptionType(str, Enum):
    """Types of exceptions in the matching process."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    OVER_INVOICED = "over_invoiced"
    UNDER_INVOICED = "under_invoiced"
    DATE_VARIANCE = "date_variance"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    OTHER = "other"


class ExceptionStatus(str, Enum):
    """Status values for exceptions."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineMatchStatus(str, Enum):
    """Status values for individual line matches."""

    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL = "partial"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"
    NO_MATCH = "no_match"
    EXCEPTION = "exception"


class CrossRefType(str, Enum):
    """Types of cross-reference entries."""

    SUPPLIER = "supplier"
    PRODUCT = "product"
    CATEGORY = "category"
    PRICE = "price"
    QUANTITY = "quantity"
    MANUAL = "manual"
    LEARNED = "learned"
