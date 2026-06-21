# models/enums.py
"""Enumerations for domain models.

Defines status enums, decision types, and other constant values
used throughout the application.
"""

import uuid
from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice processing status."""

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    """Matching engine result status."""

    PENDING = "pending"
    NO_MATCH = "no_match"
    PARTIAL_MATCH = "partial_match"
    FULL_MATCH = "full_match"
    EXCEPTION = "exception"


class MatchConfidence(str, Enum):
    """Match confidence level classification."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class DecisionType(str, Enum):
    """Matching decision outcome types."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class ExceptionStatus(str, Enum):
    """Exception handling status."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, Enum):
    """Reasons for matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    DATE_MISMATCH = "date_mismatch"
    TAX_MISMATCH = "tax_mismatch"
    MULTIPLE_POTENTIAL_MATCHES = "multiple_potential_matches"
    NO_DELIVERY_EVIDENCE = "no_delivery_evidence"
    PARTIAL_DELIVERY = "partial_delivery"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    OTHER = "other"


class CrossRefType(str, Enum):
    """Cross-reference learning record types."""

    PO_INVOICE_MATCH = "po_invoice_match"
    LINE_MATCH = "line_match"
    SUPPLIER_MATCH = "supplier_match"
    ITEM_MATCH = "item_match"
    PROMOTED_MATCH = "promoted_match"


__all__ = [
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchStatus",
    "MatchConfidence",
    "DecisionType",
    "ExceptionStatus",
    "ExceptionReason",
    "CrossRefType",
]
