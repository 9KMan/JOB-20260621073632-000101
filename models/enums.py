# models/enums.py
"""SQLAlchemy and Pydantic enum definitions."""
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
    CONFIRMED = "confirmed"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Matching decision types."""

    AUTO_APPROVE = "auto_approve"
    REVIEW = "review"
    EXCEPTION = "exception"
    REJECT = "reject"


class MatchStatus(str, enum.Enum):
    """Match record status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class ExceptionType(str, enum.Enum):
    """Exception types for matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_INVOICE = "missing_invoice"
    DUPLICATE_INVOICE = "duplicate_invoice"
    UNMATCHED_LINES = "unmatched_lines"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    TAX_VARIANCE = "tax_variance"
    CURRENCY_MISMATCH = "currency_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"


class ExceptionResolution(str, enum.Enum):
    """Exception resolution types."""

    APPROVED_AS_IS = "approved_as_is"
    ADJUSTED = "adjusted"
    MANUAL_REVIEW = "manual_review"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"
    REJECTED = "rejected"


class LineType(str, enum.Enum):
    """Line item types."""

    STANDARD = "standard"
    SERVICE = "service"
    MISCELLANEOUS = "miscellaneous"
    DISCOUNT = "discount"
    TAX = "tax"
    SHIPPING = "shipping"


class CrossRefConfidence(str, enum.Enum):
    """Confidence levels for cross-reference learning."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


class CrossRefStatus(str, enum.Enum):
    """Cross-reference record status."""

    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"
