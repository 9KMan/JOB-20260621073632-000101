# models/enums.py
"""Enumeration types for AP Automation Engine.

Defines all status and type enums used throughout the application.
"""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PAID = "paid"


class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    OPEN = "open"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class MatchingDecision(str, Enum):
    """Matching engine decision types."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_MATCHES = "multiple_matches"
    TIMING_ISSUE = "timing_issue"
    DATA_MISMATCH = "data_mismatch"


class ExceptionResolution(str, Enum):
    """Ways to resolve matching exceptions."""

    APPROVED_AS_IS = "approved_as_is"
    ADJUSTED_AND_APPROVED = "adjusted_and_approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"
    PENDING_VENDOR_RESPONSE = "pending_vendor_response"


class LineStatus(str, Enum):
    """Status values for individual invoice/PO/delivery lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CLOSED = "closed"


class BalanceType(str, Enum):
    """Types of balance ledger entries."""

    EXPECTED = "expected"
    DELIVERED = "delivered"
    INVOICED = "invoiced"
    PAID = "paid"
    VARIANCE = "variance"
    CREDIT = "credit"
