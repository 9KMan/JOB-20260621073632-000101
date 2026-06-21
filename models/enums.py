// models/enums.py
"""SQLAlchemy enums for status fields and decision types."""

import uuid
from enum import Enum

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator


class UUIDType(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class DocumentStatus(str, Enum):
    """Status for documents (invoices, POs, delivery notes)."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_MATCH = "pending_match"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class MatchStatus(str, Enum):
    """Status for matching results."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class MatchType(str, Enum):
    """Type of matching performed."""

    EXACT = "exact"
    FUZZY = "fuzzy"
    LEARNED = "learned"
    MANUAL = "manual"


class DecisionType(str, Enum):
    """Decision type for invoice matching."""

    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    REVIEW_REQUIRED = "review_required"
    EXCEPTION = "exception"


class ExceptionReason(str, Enum):
    """Reason for exception in matching."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    DUPLICATE_INVOICE = "duplicate_invoice"
    DATE_MISMATCH = "date_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH_FOUND = "no_match_found"
    PARTIAL_MATCH = "partial_match"
    LEARNING_CONFLICT = "learning_conflict"


class ExceptionStatus(str, Enum):
    """Status for exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LearningStatus(str, Enum):
    """Status for learning/cross-reference entries."""

    PENDING = "pending"
    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"
