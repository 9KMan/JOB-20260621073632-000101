# src/models/enums.py
"""Enumerations for AP Automation Core Engine.

Contains status enums, decision types, and other domain-specific constants.
"""

import enum
from typing import Any


class DocumentStatus(str, enum.Enum):
    """Status for invoices, purchase orders, and delivery notes."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    MATCHED = "matched"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PAID = "paid"


class MatchStatus(str, enum.Enum):
    """Status for the matching process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AUTO_MATCHED = "auto_matched"
    MANUAL_MATCHED = "manual_matched"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"


class DecisionType(str, enum.Enum):
    """Decision outcome for the matching engine."""

    AUTO_APPROVE = "auto_approve"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECT = "reject"
    MANUAL = "manual"


class ExceptionStatus(str, enum.Enum):
    """Status for exceptions in the matching process."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, enum.Enum):
    """Reasons why an exception was raised during matching."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    DATE_MISMATCH = "date_mismatch"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    MULTIPLE_PO_MATCH = "multiple_po_match"
    PARTIAL_MATCH = "partial_match"
    UNEXPECTED_LINE_ITEM = "unexpected_line_item"
    MISSING_LINE_ITEM = "missing_line_item"
    CURRENCY_MISMATCH = "currency_mismatch"
    TAX_MISMATCH = "tax_mismatch"
    VENDOR_MISMATCH = "vendor_mismatch"
    OTHER = "other"


class LineStatus(str, enum.Enum):
    """Status for individual invoice/PO lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    OVER_DELIVERED = "over_delivered"
    CLOSED = "closed"


class LearningStatus(str, enum.Enum):
    """Status for learned cross-references."""

    LEARNING = "learning"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    REJECTED = "rejected"


def get_enum_values(enum_class: type[enum.Enum]) -> list[str]:
    """Get all values from an enum as a list of strings.

    Args:
        enum_class: The enum class to get values from.

    Returns:
        List of enum values as strings.
    """
    return [e.value for e in enum_class]


def validate_enum_value(enum_class: type[enum.Enum], value: str) -> bool:
    """Validate that a value is a valid enum value.

    Args:
        enum_class: The enum class to validate against.
        value: The value to validate.

    Returns:
        True if the value is valid, False otherwise.
    """
    return value in get_enum_values(enum_class)
