# models/enums.py
"""Status enums and decision types for the matching engine."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Invoice processing status."""
    
    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status."""
    
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status."""
    
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_DELIVERED = "partially_delivered"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Match record status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"


class MatchDecision(str, enum.Enum):
    """Matching decision outcomes."""
    
    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    EXCEPTION = "exception"
    REQUIRES_REVIEW = "requires_review"
    NO_MATCH = "no_match"


class LineStatus(str, enum.Enum):
    """Status for individual invoice/PO lines."""
    
    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    OVER_INVOICED = "over_invoiced"
    UNDER_INVOICED = "under_invoiced"
