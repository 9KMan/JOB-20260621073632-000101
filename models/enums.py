# models/enums.py
"""Enumeration types for AP Automation Engine.

Contains all status enums, decision types, and other categorical types
used across the application.
"""

import enum


class DocumentStatus(str, enum.Enum):
    """Status of a document (Invoice, PO, Delivery Note)."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MATCHED = "matched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class MatchStatus(str, enum.Enum):
    """Status of a matching operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    MANUAL_REVIEW = "manual_review"


class MatchConfidence(str, enum.Enum):
    """Confidence level of a match."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class DecisionType(str, enum.Enum):
    """Decision type from the matching engine."""

    AUTO_APPROVE = "auto_approve"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    HOLD = "hold"


class ExceptionStatus(str, enum.Enum):
    """Status of an exception."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, enum.Enum):
    """Reason codes for exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    UNAUTHORIZED_VENDOR = "unauthorized_vendor"
    INVALID_DATE = "invalid_date"
    OVER_TOLERANCE = "over_tolerance"
    MISSING_LINE_ITEMS = "missing_line_items"
    TAX_MISMATCH = "tax_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    ACCOUNTING_CODE_MISMATCH = "accounting_code_mismatch"
    OTHER = "other"


class LedgerTransactionType(str, enum.Enum):
    """Type of transaction in the balance ledger."""

    PO_CREATED = "po_created"
    PO_AMENDED = "po_amended"
    PO_CANCELLED = "po_cancelled"
    DN_RECEIVED = "dn_received"
    DN_CANCELLED = "dn_cancelled"
    INVOICE_CREATED = "invoice_created"
    INVOICE_CANCELLED = "invoice_cancelled"
    MATCH_APPLIED = "match_applied"
    MATCH_REVERSED = "match_reversed"
    PAYMENT_MADE = "payment_made"
    CREDIT_NOTE = "credit_note"
    WRITE_OFF = "write_off"


class MatchPairStatus(str, enum.Enum):
    """Status of a matched pair in cross-reference table."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    DELETED = "deleted"
