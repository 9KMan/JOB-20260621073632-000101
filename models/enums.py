# models/enums.py
"""Enumeration types for the AP Automation system."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    
    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status enumeration."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status enumeration."""
    
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Matching decision enumeration."""
    
    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"
    NO_MATCH = "no_match"
    PENDING = "pending"


class MatchConfidence(str, enum.Enum):
    """Match confidence level enumeration."""
    
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, enum.Enum):
    """Exception type enumeration."""
    
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_MATCHES = "multiple_matches"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    DATE_VARIANCE = "date_variance"
    UNMATCHED_LINES = "unmatched_lines"


class ExceptionStatus(str, enum.Enum):
    """Exception status enumeration."""
    
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineStatus(str, enum.Enum):
    """Status for individual invoice/PO/delivery lines."""
    
    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class MatchType(str, enum.Enum):
    """Type of match between documents."""
    
    EXACT = "exact"
    FUZZY = "fuzzy"
    LEARNED = "learned"
    MANUAL = "manual"


class LearningStatus(str, enum.Enum):
    """Learning/promotion status for cross-reference entries."""
    
    PENDING = "pending"
    LEARNED = "learned"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    EXPIRED = "expired"
