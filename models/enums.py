# models/enums.py
"""
SQLAlchemy and Pydantic enum definitions.

Centralizes all status and type enums used throughout the application.
"""

import enum
from typing import Literal


class InvoiceStatus(str, enum.Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
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
    ISSUED = "issued"
    RECEIVED = "received"
    PARTIALLY_RECEIVED = "partially_received"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """
    Matching decision outcomes.
    
    Determines what action should be taken for a match.
    """

    AUTO_APPROVE = "auto_approve"
    """High confidence match - auto-approve payment"""

    REVIEW = "review"
    """Medium confidence match - requires 1-click review"""

    EXCEPTION = "exception"
    """Low confidence match - requires exception handling"""

    NO_MATCH = "no_match"
    """No matching records found"""


class MatchConfidence(str, enum.Enum):
    """Confidence level for match scores."""

    HIGH = "high"
    """Score >= threshold_high (0.95 default)"""

    MEDIUM = "medium"
    """Score >= threshold_mid (0.75 default)"""

    LOW = "low"
    """Score >= threshold_low (0.50 default)"""

    NONE = "none"
    """Score < threshold_low"""


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    """Invoice price differs from PO price beyond tolerance"""

    QUANTITY_VARIANCE = "quantity_variance"
    """Invoice quantity differs from PO quantity beyond tolerance"""

    NO_PO_FOUND = "no_po_found"
    """No matching purchase order found"""

    DUPLICATE_INVOICE = "duplicate_invoice"
    """Potential duplicate invoice detected"""

    PARTIAL_MATCH = "partial_match"
    """Only some invoice lines matched"""

    PO_CLOSED = "po_closed"
    """Purchase order is closed/cancelled"""

    EXPIRED_DELIVERY = "expired_delivery"
    """Delivery note is expired or outside valid window"""


class ExceptionStatus(str, enum.Enum):
    """Status of exceptions in the exception queue."""

    OPEN = "open"
    """Exception is open and awaiting resolution"""

    IN_REVIEW = "in_review"
    """Exception is being reviewed"""

    RESOLVED = "resolved"
    """Exception has been resolved by user"""

    DISMISSED = "dismissed"
    """Exception has been dismissed by user"""

    ESCALATED = "escalated"
    """Exception has been escalated"""


class PaymentStatus(str, enum.Enum):
    """Payment processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
