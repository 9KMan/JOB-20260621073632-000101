# models/enums.py
"""SQLAlchemy and Pydantic enums for the application."""

import enum
from typing import Literal

from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column


class InvoiceStatus(str, enum.Enum):
    """Status of an invoice in the system."""

    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status of a purchase order."""

    DRAFT = "draft"
    ACTIVE = "active"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Status of a delivery note."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class MatchingDecision(str, enum.Enum):
    """Decision from the matching engine."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVED = "one_click_approved"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PENDING = "pending"


class MatchStatus(str, enum.Enum):
    """Status of a match record."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class ExceptionType(str, enum.Enum):
    """Types of exceptions in the matching process."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH = "no_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DUPLICATE_PO = "duplicate_po"
    DATE_VARIANCE = "date_variance"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    OTHER = "other"


class ExceptionStatus(str, enum.Enum):
    """Status of an exception."""

    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, enum.Enum):
    """Confidence level of a match."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


# SQLAlchemy enum columns
def create_enum_column(
    enum_class: type[enum.Enum],
    **kwargs,
) -> Mapped[enum.Enum]:
    """Helper to create a mapped column for an enum."""
    return mapped_column(
        SQLEnum(enum_class, native_enum=False, create_constraint=True),
        **kwargs,
    )
