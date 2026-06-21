# models/enums.py
"""Enumeration types for the AP Automation engine."""
import enum


class DocumentStatus(str, enum.Enum):
    """Status for documents (Invoice, PO, DN)."""

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class LineStatus(str, enum.Enum):
    """Status for individual document lines."""

    OPEN = "open"
    FULLY_MATCHED = "fully_matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"
    CLOSED = "closed"


class MatchDecision(str, enum.Enum):
    """Matching decision outcome."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    PENDING = "pending"


class MatchType(str, enum.Enum):
    """Type of matching performed."""

    EXACT = "exact"
    FUZZY = "fuzzy"
    LEARNED = "learned"
    PARTIAL = "partial"
    NONE = "none"


class DecisionStatus(str, enum.Enum):
    """Status of a matching decision."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class ExceptionStatus(str, enum.Enum):
    """Status of an exception."""

    OPEN = "open"
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
    INVALID_VENDOR = "invalid_vendor"
    INVALID_DATE = "invalid_date"
    PARTIAL_DELIVERY = "partial_delivery"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    TAX_MISMATCH = "tax_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    PO_LINE_NOT_FOUND = "po_line_not_found"
    DN_LINE_NOT_FOUND = "dn_line_not_found"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH_FOUND = "no_match_found"
    OTHER = "other"
