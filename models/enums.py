// models/enums.py
"""Enum definitions for the AP Automation Engine."""

import enum


class DocumentStatus(str, enum.Enum):
    """Status for documents (invoices, POs, delivery notes)."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class MatchStatus(str, enum.Enum):
    """Status for matching operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DecisionType(str, enum.Enum):
    """Decision types for matching results."""

    AUTO_APPROVED = "auto_approved"
    REVIEW = "review"
    EXCEPTION = "exception"
    MANUAL_OVERRIDE = "manual_override"


class ExceptionStatus(str, enum.Enum):
    """Status for exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, enum.Enum):
    """Reasons for exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    EXCEEDS_PO_AMOUNT = "exceeds_po_amount"
    UNRECOGNIZED_VENDOR = "unrecognized_vendor"
    INVALID_DATE = "invalid_date"
    CURRENCY_MISMATCH = "currency_mismatch"
    TAX_MISMATCH = "tax_mismatch"
    OTHER = "other"


class MatchConfidence(str, enum.Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class LineItemStatus(str, enum.Enum):
    """Status for line items within documents."""

    OPEN = "open"
    PARTIALLY_INVOICED = "partially_invoiced"
    FULLY_INVOICED = "fully_invoiced"
    OVER_INVOICED = "over_invoiced"
    CLOSED = "closed"


class LearningStatus(str, enum.Enum):
    """Status for cross-reference learning records."""

    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"
