# src/models/enums.py
"""Enumeration types for the AP Automation engine."""

from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""
    
    DRAFT = "draft"
    PENDING = "pending"
    RECEIVED = "received"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status enumeration."""
    
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status enumeration."""
    
    DRAFT = "draft"
    ISSUED = "issued"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """Matching decision types."""
    
    AUTO_APPROVE = "auto_approve"
    ONE_CLICK_APPROVE = "one_click_approve"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"


class MatchStatus(str, Enum):
    """Overall matching status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_MATCH_FOUND = "no_match_found"


class LineMatchStatus(str, Enum):
    """Line-level matching status."""
    
    UNMATCHED = "unmatched"
    PARTIAL_MATCH = "partial_match"
    FULL_MATCH = "full_match"
    OVER_MATCHED = "over_matched"
    MULTIPLE_MATCHES = "multiple_matches"


class ExceptionType(str, Enum):
    """Exception types for matching discrepancies."""
    
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_INVOICE = "missing_invoice"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DUPLICATE_PO = "duplicate_po"
    DATE_VARIANCE = "date_variance"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    TAX_VARIANCE = "tax_variance"
    MULTIPLE_MATCHES = "multiple_matches"
    PO_EXPIRED = "po_expired"
    PO_EXHAUSTED = "po_exhausted"


class ExceptionStatus(str, Enum):
    """Exception resolution status."""
    
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, Enum):
    """Match confidence levels."""
    
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
