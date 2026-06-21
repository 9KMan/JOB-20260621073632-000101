# models/enums.py
"""SQLAlchemy and Pydantic enums for the application."""

import uuid
from enum import Enum
from typing import Annotated

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from pydantic import BaseModel, ConfigDict


class DocumentStatus(str, Enum):
    """Status for documents (Invoice, PO, DN)."""

    DRAFT = "draft"
    PENDING = "pending"
    PROCESSING = "processing"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class LineStatus(str, Enum):
    """Status for document lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class MatchingStatus(str, Enum):
    """Status for the matching process."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchingDecision(str, Enum):
    """Decision result from matching."""

    AUTO_APPROVED = "auto_approved"
    REVIEW_REQUIRED = "review_required"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_MATCHES = "multiple_matches"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_VARIANCE = "date_variance"
    DELIVERY_VARIANCE = "delivery_variance"
    OTHER = "other"


class ExceptionStatus(str, Enum):
    """Status of exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, Enum):
    """Reasons for exceptions."""

    PRICE_TOO_HIGH = "price_too_high"
    PRICE_TOO_LOW = "price_too_low"
    QUANTITY_EXCEEDS_PO = "quantity_exceeds_po"
    QUANTITY_UNDER_PO = "quantity_under_po"
    NO_PO_REFERENCE = "no_po_reference"
    MULTIPLE_PO_CANDIDATES = "multiple_po_candidates"
    INVOICE_ALREADY_EXISTS = "invoice_already_exists"
    INVOICE_DATE_MISMATCH = "invoice_date_mismatch"
    DELIVERY_DATE_MISMATCH = "delivery_date_mismatch"
    PARTIAL_DELIVERY = "partial_delivery"
    MANUAL_OVERRIDE = "manual_override"
    UNKNOWN = "unknown"


class MatchConfidence(str, Enum):
    """Confidence levels for matches."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


# Custom SQLAlchemy type for storing enum values as strings
class EnumType(TypeDecorator):
    """Abstract base for enum type columns."""

    impl = String(50)
    cache_ok = True

    def __init__(self, enum_class: type[Enum]) -> None:
        super().__init__()
        self.enum_class = enum_class

    def process_bind_param(self, value: Enum | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, Enum):
            return value.value
        return value

    def process_result_value(self, value: str | None) -> Enum | None:
        if value is None:
            return None
        for item in self.enum_class:
            if item.value == value:
                return item
        raise ValueError(f"Unknown {self.enum_class.__name__} value: {value}")


# Pydantic models for enum choices/lists
class EnumChoice(BaseModel):
    """Model for enum choice display."""

    value: str
    label: str
    description: str | None = None


def get_document_status_choices() -> list[EnumChoice]:
    """Get display choices for DocumentStatus."""
    return [
        EnumChoice(value=s.value, label=s.name.replace("_", " ").title(), description=None)
        for s in DocumentStatus
    ]


def get_matching_decision_choices() -> list[EnumChoice]:
    """Get display choices for MatchingDecision."""
    descriptions = {
        MatchingDecision.AUTO_APPROVED: "Automatically approved based on high confidence score",
        MatchingDecision.REVIEW_REQUIRED: "Requires 1-click review due to medium confidence",
        MatchingDecision.EXCEPTION: "Exception raised, needs manual intervention",
        MatchingDecision.NO_MATCH: "No matching PO found",
    }
    return [
        EnumChoice(value=s.value, label=s.name.replace("_", " ").title(), description=descriptions.get(s))
        for s in MatchingDecision
    ]


def get_exception_type_choices() -> list[EnumChoice]:
    """Get display choices for ExceptionType."""
    return [
        EnumChoice(value=s.value, label=s.name.replace("_", " ").title(), description=None)
        for s in ExceptionType
    ]


def get_exception_status_choices() -> list[EnumChoice]:
    """Get display choices for ExceptionStatus."""
    return [
        EnumChoice(value=s.value, label=s.name.replace("_", " ").title(), description=None)
        for s in ExceptionStatus
    ]
