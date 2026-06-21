# models/enums.py
"""Enumeration types for the AP Automation system."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    MATCHING_IN_PROGRESS = "matching_in_progress"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DeliveryNoteStatus(str, enum.Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    FULLY_INVOICED = "fully_invoiced"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Status values for invoice-PO matching."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Decision outcomes from the matching engine."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class LineStatus(str, enum.Enum):
    """Status values for invoice/PO/delivery note lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


class ExceptionType(str, enum.Enum):
    """Types of exceptions detected during matching."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    DATE_VARIANCE = "date_variance"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    PARTIAL_DELIVERY = "partial_delivery"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    PO_EXPIRED = "po_expired"
    PO_CLOSED = "po_closed"
    INVALID_VENDOR = "invalid_vendor"
    TAX_MISMATCH = "tax_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"


class ExceptionSeverity(str, enum.Enum):
    """Severity levels for exceptions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExceptionResolution(str, enum.Enum):
    """Possible resolutions for exceptions."""

    APPROVED_AS_IS = "approved_as_is"
    ADJUSTED_AND_APPROVED = "adjusted_and_approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class CrossRefType(str, enum.Enum):
    """Types of cross-reference learning entries."""

    VENDOR_PRODUCT = "vendor_product"
    VENDOR_ACCOUNT = "vendor_account"
    VENDOR_TERM = "vendor_term"
    VENDOR_PRICE = "vendor_price"


class LearningStatus(str, enum.Enum):
    """Status of learning/promotion in cross-reference table."""

    ACTIVE = "active"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    EXPIRED = "expired"
