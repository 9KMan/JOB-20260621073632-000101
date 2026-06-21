# models/enums.py
"""SQLAlchemy-enum types and Pydantic-compatible Python enums."""

import uuid
from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy.types import TypeDecorator


# ── Python Enums (Pydantic-compatible) ───────────────────────────────────────


class InvoiceStatus(str, Enum):
    """Lifecycle status of an invoice."""

    DRAFT = "draft"
    RECEIVED = "received"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PAID = "paid"


class POStatus(str, Enum):
    """Lifecycle status of a purchase order."""

    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    FULLY_RECEIVED = "fully_received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Lifecycle status of a delivery note."""

    RECEIVED = "received"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CLOSED = "closed"
    DISPUTED = "disputed"


class MatchDecision(str, Enum):
    """Decision output of the matching engine."""

    AUTO_APPROVED = "auto_approved"
    REVIEW = "review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class ExceptionType(str, Enum):
    """Types of matching exceptions requiring human review."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DESCRIPTION_MISMATCH = "description_mismatch"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_POTENTIAL_MATCHES = "multiple_potential_matches"
    CROSS_COMPANY = "cross_company"
    CURRENCY_MISMATCH = "currency_mismatch"
    TAX_MISMATCH = "tax_mismatch"


class ExceptionStatus(str, Enum):
    """Resolution status of an exception."""

    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


# ── SQLAlchemy Enum Types ────────────────────────────────────────────────────


def _sa_enum(name: str, enum_cls: type[Enum]) -> SAEnum:
    """Create a SQLAlchemy Enum type with the given Python enum class."""
    return SAEnum(enum_cls, name=name, create_constraint=True, native_enum=True)


# These types are used in model column definitions
InvoiceStatusType = _sa_enum("invoice_status", InvoiceStatus)
POStatusType = _sa_enum("po_status", POStatus)
DeliveryNoteStatusType = _sa_enum("delivery_note_status", DeliveryNoteStatus)
MatchDecisionType = _sa_enum("match_decision", MatchDecision)
ExceptionTypeType = _sa_enum("exception_type", ExceptionType)
ExceptionStatusType = _sa_enum("exception_status", ExceptionStatus)
