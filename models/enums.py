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
    REVIEW = "review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    APPROVED = "approved"
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
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class MatchingDecision(str, enum.Enum):
    """Matching decision outcomes."""
    
    AUTO_APPROVE = "auto_approve"
    REVIEW = "review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class MatchConfidence(str, enum.Enum):
    """Match confidence levels."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""
    
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_MATCHES = "multiple_matches"
    PARTIAL_MATCH = "partial_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"


class ExceptionStatus(str, enum.Enum):
    """Status values for exceptions."""
    
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineItemStatus(str, enum.Enum):
    """Status values for line items."""
    
    PENDING = "pending"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    EXCEPTION = "exception"
