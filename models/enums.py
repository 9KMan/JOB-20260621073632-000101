// models/enums.py
"""SQLAlchemy enums for status fields and decision types.

This module defines all enumerated types used across models:
- Document status (draft, submitted, approved, etc.)
- Matching status and decisions
- Exception types and resolutions
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID


def uuid_enum_parameter() -> uuid.UUID:
    """Generate UUID for enum parameter."""
    return uuid.uuid4()


# Use PostgreSQL enum type for database storage
# Status enums
DocumentStatus = UUID  # Will be used as string enum in Python


class DocumentStatusType(str, PyEnum):
    """Document status enumeration.

    Represents the lifecycle status of documents.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class InvoiceStatusType(str, PyEnum):
    """Invoice-specific status enumeration.

    Extends document status for invoice-specific states.
    """

    DRAFT = "draft"
    RECEIVED = "received"
    PENDING_MATCH = "pending_match"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatusType(str, PyEnum):
    """Purchase Order status enumeration."""

    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MatchStatusType(str, PyEnum):
    """Matching process status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_MATCH_FOUND = "no_match_found"


class MatchDecisionType(str, PyEnum):
    """Matching decision result enumeration.

    Determines how an invoice should be processed based on matching score.
    """

    AUTO_APPROVED = "auto_approved"
    REVIEW_REQUIRED = "review_required"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


class ExceptionTypeType(str, PyEnum):
    """Exception type enumeration.

    Categorizes different types of matching exceptions.
    """

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    MISSING_LINE_ITEM = "missing_line_item"
    PARTIAL_MATCH = "partial_match"
    OVER_INVOICED = "over_invoiced"
    UNDER_INVOICED = "under_invoiced"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"
    UNKNOWN = "unknown"


class ExceptionResolutionType(str, PyEnum):
    """Exception resolution enumeration.

    Represents how an exception was resolved.
    """

    PENDING = "pending"
    APPROVED_AS_IS = "approved_as_is"
    ADJUSTED = "adjusted"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
    WRITE_OFF = "write_off"
    MANUAL_OVERRIDE = "manual_override"


# SQLAlchemy Enum columns for database
InvoiceStatus = InvoiceStatusType
PurchaseOrderStatus = PurchaseOrderStatusType
MatchStatus = MatchStatusType
MatchDecision = MatchDecisionType
ExceptionType = ExceptionTypeType
ExceptionResolution = ExceptionResolutionType
DocumentStatus = DocumentStatusType
