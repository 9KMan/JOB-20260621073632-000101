// models/enums.py
"""
Enumeration types used throughout the application.

These enums define the allowed values for status fields, decision types,
and other categorical data in the system.
"""

import uuid
from enum import Enum
from typing import Literal

from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class InvoiceStatus(str, Enum):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchingDecision(str, Enum):
    """
    Decision outcomes from the matching engine.
    
    These decisions determine the next action for matched records.
    """

    AUTO_APPROVED = "auto_approved"
    """High confidence match - automatically approved for payment"""

    REVIEW_REQUIRED = "review_required"
    """Medium confidence match - requires human review"""

    EXCEPTION = "exception"
    """Low confidence match or discrepancy - requires investigation"""

    NO_MATCH = "no_match"
    """No matching records found"""

    PENDING = "pending"
    """Matching in progress or awaiting processing"""


class MatchConfidence(str, Enum):
    """
    Confidence levels for individual match scores.
    
    These are derived from the weighted scoring algorithm.
    """

    VERY_HIGH = "very_high"
    """Confidence >= 95%"""

    HIGH = "high"
    """Confidence >= 85% and < 95%"""

    MEDIUM = "medium"
    """Confidence >= 70% and < 85%"""

    LOW = "low"
    """Confidence >= 50% and < 70%"""

    VERY_LOW = "very_low"
    """Confidence < 50%"""


class LineStatus(str, Enum):
    """Status values for invoice/POL/DN lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    OVER_DELIVERED = "over_delivered"
    CLOSED = "closed"


class ExceptionType(str, Enum):
    """Types of matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    """Unit price differs beyond tolerance"""

    QUANTITY_MISMATCH = "quantity_mismatch"
    """Quantity differs beyond tolerance"""

    MISSING_PO = "missing_po"
    """Invoice has no matching purchase order"""

    MISSING_DN = "missing_dn"
    """Invoice/POL has no matching delivery note"""

    DUPLICATE = "duplicate"
    """Potential duplicate invoice detected"""

    OVER_DELIVERY = "over_delivery"
    """Delivery exceeds ordered quantity"""

    EXPIRED = "expired"
    """PO has expired or been cancelled"""

    SPLIT_MATCH = "split_match"
    """Single invoice matches multiple POs/DNs"""


class ExceptionStatus(str, Enum):
    """Status of matching exceptions."""

    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


# SQLAlchemy enum columns (for use in model definitions)
invoice_status_enum = SQLEnum(
    InvoiceStatus,
    name="invoice_status",
    create_constraint=True,
    validate_string=True,
)

po_status_enum = SQLEnum(
    PurchaseOrderStatus,
    name="po_status",
    create_constraint=True,
    validate_string=True,
)

dn_status_enum = SQLEnum(
    DeliveryNoteStatus,
    name="dn_status",
    create_constraint=True,
    validate_string=True,
)

matching_decision_enum = SQLEnum(
    MatchingDecision,
    name="matching_decision",
    create_constraint=True,
    validate_string=True,
)

match_confidence_enum = SQLEnum(
    MatchConfidence,
    name="match_confidence",
    create_constraint=True,
    validate_string=True,
)

line_status_enum = SQLEnum(
    LineStatus,
    name="line_status",
    create_constraint=True,
    validate_string=True,
)

exception_type_enum = SQLEnum(
    ExceptionType,
    name="exception_type",
    create_constraint=True,
    validate_string=True,
)

exception_status_enum = SQLEnum(
    ExceptionStatus,
    name="exception_status",
    create_constraint=True,
    validate_string=True,
)
