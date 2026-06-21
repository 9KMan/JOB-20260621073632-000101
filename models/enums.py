// models/enums.py
"""Enumeration types for AP Automation Engine.

Defines all status enums and decision types used across models.
"""

import enum


class InvoiceStatus(str, enum.Enum):
    """Invoice processing status."""
    
    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status."""
    
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status."""
    
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIAL = "partial"
    COMPLETE = "complete"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Matching process status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Matching decision based on score thresholds."""
    
    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class LineStatus(str, enum.Enum):
    """Line item status within a document."""
    
    OPEN = "open"
    PARTIAL = "partial"
    FULL = "full"
    CLOSED = "closed"


class ExceptionStatus(str, enum.Enum):
    """Exception handling status."""
    
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""
    
    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"
    MULTIPLE_POTENTIAL_MATCHES = "multiple_potential_matches"
    AMOUNT_VARIANCE = "amount_variance"
    UNMATCHED_LINES = "unmatched_lines"


class MatchConfidence(str, enum.Enum):
    """Confidence level of a match."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LearningStatus(str, enum.Enum):
    """Learning/cross-reference status."""
    
    ACTIVE = "active"
    LEARNING = "learning"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    ARCHIVED = "archived"
