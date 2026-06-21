# models/enums.py
"""Enum definitions for the AP Automation system."""

import uuid
from enum import Enum
from typing import Any


class StrEnum(str, Enum):
    """Base enum that inherits from str for JSON serialization."""

    def __json__(self) -> str:
        """Return string value for JSON serialization."""
        return str(self.value)


class DocumentStatus(StrEnum):
    """Status for documents (PO, Invoice, DN)."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    MATCHED = "matched"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class InvoiceStatus(DocumentStatus):
    """Extended status for invoices, inherits from DocumentStatus."""

    RECEIVED = "received"
    VALIDATED = "validated"
    MATCHING = "matching"


class PurchaseOrderStatus(DocumentStatus):
    """Extended status for purchase orders."""

    OPEN = "open"
    PARTIALLY_RECEIVED = "partially_received"
    CLOSED = "closed"


class LineStatus(StrEnum):
    """Status for individual invoice/DN lines."""

    OPEN = "open"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    OVER_DELIVERED = "over_delivered"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"


class MatchDecision(StrEnum):
    """
    Matching decision outcomes.
    
    - AUTO_APPROVED: Score >= threshold_high, auto-matched and approved
    - REVIEW: Score between threshold_mid and threshold_high, needs 1-click review
    - EXCEPTION: Score between threshold_low and threshold_mid, needs exception handling
    - REJECTED: Score < threshold_low, auto-rejected
    """

    AUTO_APPROVED = "auto_approved"
    REVIEW = "review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PENDING = "pending"


class MatchScoreLevel(StrEnum):
    """Score level categories for matching results."""

    HIGH = "high"  # 95-100
    MEDIUM = "medium"  # 70-94
    LOW = "low"  # 40-69
    VERY_LOW = "very_low"  # 0-39


class DecisionStatus(StrEnum):
    """Status for matching decisions."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    OVERRIDDEN = "overridden"


class ExceptionReason(StrEnum):
    """Reasons for matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MULTIPLE_PO_MATCHES = "multiple_po_matches"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PO_CLOSED = "po_closed"
    LINE_EXCEEDED = "line_exceeded"
    TAX_MISMATCH = "tax_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"
    OTHER = "other"


class LearningAction(StrEnum):
    """Actions taken by the learning loop."""

    LEARNED = "learned"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


def get_match_decision(
    score: float,
    threshold_high: int = 95,
    threshold_mid: int = 70,
    threshold_low: int = 40,
) -> MatchDecision:
    """
    Determine match decision based on score and thresholds.

    Args:
        score: Match score (0-100)
        threshold_high: Auto-approve threshold
        threshold_mid: Review threshold
        threshold_low: Exception threshold

    Returns:
        MatchDecision enum value
    """
    if score >= threshold_high:
        return MatchDecision.AUTO_APPROVED
    elif score >= threshold_mid:
        return MatchDecision.REVIEW
    elif score >= threshold_low:
        return MatchDecision.EXCEPTION
    else:
        return MatchDecision.REJECTED


def get_score_level(score: float) -> MatchScoreLevel:
    """
    Categorize a score into a level.

    Args:
        score: Match score (0-100)

    Returns:
        MatchScoreLevel enum value
    """
    if score >= 95:
        return MatchScoreLevel.HIGH
    elif score >= 70:
        return MatchScoreLevel.MEDIUM
    elif score >= 40:
        return MatchScoreLevel.LOW
    else:
        return MatchScoreLevel.VERY_LOW
