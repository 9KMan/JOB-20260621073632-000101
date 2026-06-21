// models/enums.py
"""SQLAlchemy and Pydantic enums for the AP Automation Engine.

These enums define the valid states and types throughout the system.
"""

import enum
from typing import Annotated

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class InvoiceStatus(str, enum.Enum):
    """Status of an invoice in the system."""

    DRAFT = "draft"
    PENDING_MATCHING = "pending_matching"
    MATCHED = "matched"
    AUTO_APPROVED = "auto_approved"
    UNDER_REVIEW = "under_review"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status of a purchase order."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Status of a delivery note."""

    DRAFT = "draft"
    RECEIVED = "received"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class ExceptionStatus(str, enum.Enum):
    """Status of a matching exception."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ExceptionReason(str, enum.Enum):
    """Reason codes for matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    PARTIAL_DELIVERY = "partial_delivery"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    DATE_VARIANCE = "date_variance"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH = "no_match"
    OTHER = "other"


class MatchDecision(str, enum.Enum):
    """Matching engine decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    REVIEW = "review"
    EXCEPTION = "exception"


class DecisionType(str, enum.Enum):
    """Type of matching decision."""

    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    EXCEPTION = "exception"
    MANUAL = "manual"


class LineMatchStatus(str, enum.Enum):
    """Status of a line-level match."""

    PENDING = "pending"
    MATCHED = "matched"
    OVER_MATCHED = "over_matched"
    UNDER_MATCHED = "under_matched"
    UNMATCHED = "unmatched"


class MatchConfirmation(str, enum.Enum):
    """Confirmation status for learning loop."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class PydanticEnumMixin:
    """Mixin to provide Pydantic schema support for enums."""

    @classmethod
    def get_pydantic_schema(cls, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Return Pydantic-compatible schema for the enum."""
        return core_schema.nullable_schema(
            inner_schema=core_schema.enum_schema(
                list(cls),
                serialization=core_schema.to_string_enum_serialization(cls),
            )
        )


# Annotated types for better IDE support
InvoiceStatusType = Annotated[InvoiceStatus, PydanticEnumMixin]
PurchaseOrderStatusType = Annotated[PurchaseOrderStatus, PydanticEnumMixin]
DeliveryNoteStatusType = Annotated[DeliveryNoteStatus, PydanticEnumMixin]
ExceptionStatusType = Annotated[ExceptionStatus, PydanticEnumMixin]
MatchDecisionType = Annotated[MatchDecision, PydanticEnumMixin]
DecisionTypeType = Annotated[DecisionType, PydanticEnumMixin]
