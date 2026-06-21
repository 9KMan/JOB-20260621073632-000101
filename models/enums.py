// models/enums.py
"""Enumeration types for the AP Automation Engine."""
import enum


class InvoiceStatus(str, enum.Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Match decision outcomes."""

    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class MatchStatus(str, enum.Enum):
    """Status of match records."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_MATCHES = "multiple_matches"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"
    OTHER = "other"


class ExceptionStatus(str, enum.Enum):
    """Status of exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LedgerEntryType(str, enum.Enum):
    """Types of balance ledger entries."""

    PO_INITIAL = "po_initial"
    DN_RECEIPT = "dn_receipt"
    INVOICE_MATCH = "invoice_match"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"
    CLOSEOUT = "closeout"


class MatchConfidenceLevel(str, enum.Enum):
    """Confidence levels for match scores."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
