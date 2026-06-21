# models/enums.py
"""SQLAlchemy enum types for status fields and decision types.

These enums map to PostgreSQL enum types.
"""

import enum


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status enumeration."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXCEPTION = "exception"


class MatchDecision(str, enum.Enum):
    """Matching engine decision types."""

    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    PENDING = "pending"
    DISPUTED = "disputed"


class MatchConfidence(str, enum.Enum):
    """Match confidence levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    OVERDELIVERY = "overdelivery"
    UNDERDELIVERY = "underdelivery"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"


class ExceptionResolution(str, enum.Enum):
    """Exception resolution statuses."""

    PENDING = "pending"
    APPROVED_WITH_EXCEPTION = "approved_with_exception"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
