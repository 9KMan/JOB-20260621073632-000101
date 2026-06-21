# models/enums.py
"""Enumeration types for AP Automation Engine.

Contains all status enums and decision types used across the system.
"""

import enum


class DocumentStatus(str, enum.Enum):
    """Status for documents (PO, Invoice, Delivery Note)."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    MATCHED = "matched"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class InvoiceStatus(str, enum.Enum):
    """Status for invoices."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PENDING_MATCH = "pending_match"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status for purchase orders."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(str, enum.Enum):
    """Status for delivery notes."""

    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    PARTIAL_RECEIPT = "partial_receipt"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchingStatus(str, enum.Enum):
    """Status for matching operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DecisionType(str, enum.Enum):
    """Decision types for matching results."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    MANUAL_REVIEW = "manual_review"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class ExceptionReason(str, enum.Enum):
    """Reasons for matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PURCHASE_ORDER = "missing_purchase_order"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    DATE_MISMATCH = "date_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    TAX_MISMATCH = "tax_mismatch"
    DUPLICATE_LINE = "duplicate_line"
    NO_MATCHING_PO_LINES = "no_matching_po_lines"
    AMOUNT_EXCEEDS_PO = "amount_exceeds_po"
    ORPHANED_DELIVERY_NOTE = "orphaned_delivery_note"
    CONFLICTING_MATCHES = "conflicting_matches"


class ExceptionStatus(str, enum.Enum):
    """Status for exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, enum.Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class BalanceType(str, enum.Enum):
    """Balance types for ledger entries."""

    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"
    DELIVERY_NOTE = "delivery_note"
