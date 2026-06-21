# models/enums.py
"""Enumeration types for the AP Automation Engine."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status values."""
    
    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status values."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status values."""
    
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class MatchingDecision(str, Enum):
    """Matching decision outcomes."""
    
    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PENDING = "pending"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""
    
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH = "no_match"
    PARTIAL_MATCH = "partial_match"


class ExceptionStatus(str, Enum):
    """Status of matching exceptions."""
    
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, Enum):
    """Match confidence levels."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
