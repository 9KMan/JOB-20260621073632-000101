# models/enums.py
"""Enum definitions for the AP Automation Engine."""

import enum


class DocumentStatus(str, enum.Enum):
    """Status for documents (PO, Invoice, DN)."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class InvoiceStatus(str, enum.Enum):
    """Status specific to invoices."""

    DRAFT = "draft"
    RECEIVED = "received"
    PENDING_MATCH = "pending_match"
    MATCHED = "matched"
    MATCHED_WITH_EXCEPTIONS = "matched_with_exceptions"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status specific to purchase orders."""

    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Status for matching operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class LineMatchStatus(str, enum.Enum):
    """Status for individual line matching."""

    PENDING = "pending"
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"
    NO_MATCH = "no_match"
    EXCEPTION = "exception"


class MatchConfidence(str, enum.Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class DecisionType(str, enum.Enum):
    """Decision types for matching engine."""

    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"


class ExceptionStatus(str, enum.Enum):
    """Status for exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, enum.Enum):
    """Reasons for exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    DUPLICATE_INVOICE = "duplicate_invoice"
    TAX_VARIANCE = "tax_variance"
    DELIVERY_DATE_VARIANCE = "delivery_date_variance"
    CURRENCY_MISMATCH = "currency_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"
    OTHER = "other"


class LedgerTransactionType(str, enum.Enum):
    """Types of ledger transactions."""

    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    CREDIT_NOTE = "credit_note"
    ADJUSTMENT = "adjustment"
    CLOSURE = "closure"


class ConfidenceLevel(str, enum.Enum):
    """Confidence levels for cross-reference learning."""

    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    UNVERIFIED = "unverified"


class MatchType(str, enum.Enum):
    """Types of matches."""

    PO_MATCH = "po_match"
    DN_MATCH = "dn_match"
    PARTIAL_MATCH = "partial_match"
    VARIANCE_MATCH = "variance_match"
