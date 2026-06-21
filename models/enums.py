// models/enums.py
"""Enumeration types for AP Automation Core Engine.

This module defines all enum types used throughout the application
for status fields, decision types, and other categorical data.

All enums use string values for database storage to ensure
cross-database compatibility and human-readable values.
"""

import enum
from typing import Any, Dict, List


class InvoiceStatus(str, enum.Enum):
    """Invoice status values.
    
    Represents the lifecycle states of an invoice from ingestion
    through matching and final processing.
    """
    
    DRAFT = "draft"
    RECEIVED = "received"
    VALIDATED = "validated"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"
    
    @classmethod
    def active_statuses(cls) -> List["InvoiceStatus"]:
        """Get list of active (non-terminal) statuses."""
        return [
            cls.DRAFT,
            cls.RECEIVED,
            cls.VALIDATED,
            cls.MATCHING,
            cls.MATCHED,
            cls.EXCEPTION,
        ]
    
    @classmethod
    def terminal_statuses(cls) -> List["InvoiceStatus"]:
        """Get list of terminal statuses."""
        return [
            cls.APPROVED,
            cls.REJECTED,
            cls.PAID,
            cls.CANCELLED,
        ]
    
    def is_terminal(self) -> bool:
        """Check if this status is terminal."""
        return self in self.terminal_statuses()


class PurchaseOrderStatus(str, enum.Enum):
    """Purchase order status values."""
    
    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    
    @classmethod
    def active_statuses(cls) -> List["PurchaseOrderStatus"]:
        """Get list of active statuses."""
        return [
            cls.DRAFT,
            cls.SENT,
            cls.ACKNOWLEDGED,
            cls.PARTIALLY_RECEIVED,
            cls.RECEIVED,
        ]


class DeliveryNoteStatus(str, enum.Enum):
    """Delivery note status values."""
    
    DRAFT = "draft"
    ISSUED = "issued"
    RECEIVED = "received"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    
    @classmethod
    def active_statuses(cls) -> List["DeliveryNoteStatus"]:
        """Get list of active statuses."""
        return [
            cls.DRAFT,
            cls.ISSUED,
            cls.RECEIVED,
            cls.PARTIALLY_MATCHED,
        ]


class MatchStatus(str, enum.Enum):
    """Match status values.
    
    Represents the state of a match between invoice lines
    and their corresponding PO/DN lines.
    """
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @classmethod
    def active_statuses(cls) -> List["MatchStatus"]:
        """Get list of active statuses."""
        return [cls.PENDING, cls.IN_PROGRESS]


class MatchDecision(str, enum.Enum):
    """Match decision values.
    
    Represents the outcome of the matching algorithm,
    determining whether an invoice can be auto-approved
    or needs human review.
    """
    
    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
    NO_MATCH = "no_match"
    
    @classmethod
    def from_score(cls, score: float, thresholds: Dict[str, float]) -> "MatchDecision":
        """Determine decision based on match score and thresholds.
        
        Args:
            score: Match score (0-100).
            thresholds: Dict with 'high', 'mid', 'low' threshold values.
        
        Returns:
            MatchDecision based on score and thresholds.
        """
        high = thresholds.get("high", 95)
        mid = thresholds.get("mid", 75)
        low = thresholds.get("low", 50)
        
        if score >= high:
            return cls.AUTO_APPROVED
        elif score >= mid:
            return cls.ONE_CLICK_REVIEW
        elif score >= low:
            return cls.EXCEPTION
        else:
            return cls.MANUAL_REVIEW
    
    def requires_review(self) -> bool:
        """Check if this decision requires human review."""
        return self in [
            self.ONE_CLICK_REVIEW,
            self.EXCEPTION,
            self.MANUAL_REVIEW,
        ]


class ExceptionType(str, enum.Enum):
    """Exception types for unmatched invoices.
    
    Categorizes the type of matching exception to help
    determine the appropriate resolution workflow.
    """
    
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_PO = "multiple_po"
    PARTIAL_MATCH = "partial_match"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    INVALID_LINE = "invalid_line"
    BLOCKED_VENDOR = "blocked_vendor"
    OTHER = "other"
    
    @classmethod
    def variance_types(cls) -> List["ExceptionType"]:
        """Get exception types related to value/quantity variances."""
        return [
            cls.PRICE_VARIANCE,
            cls.QUANTITY_VARIANCE,
            cls.OVER_DELIVERY,
            cls.UNDER_DELIVERY,
        ]
    
    @classmethod
    def missing_document_types(cls) -> List["ExceptionType"]:
        """Get exception types related to missing documents."""
        return [
            cls.MISSING_PO,
            cls.MISSING_DELIVERY_NOTE,
        ]


class ExceptionStatus(str, enum.Enum):
    """Exception status values."""
    
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
    
    @classmethod
    def active_statuses(cls) -> List["ExceptionStatus"]:
        """Get list of active (unresolved) statuses."""
        return [cls.OPEN, cls.IN_REVIEW, cls.ESCALATED]


class LineStatus(str, enum.Enum):
    """Status for individual document lines."""
    
    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    
    @classmethod
    def matched_statuses(cls) -> List["LineStatus"]:
        """Get statuses indicating successful matching."""
        return [cls.MATCHED, cls.PARTIALLY_MATCHED]


class LearningStatus(str, enum.Enum):
    """Learning/cross-reference status values."""
    
    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"
    
    def promote(self) -> "LearningStatus":
        """Promote a cross-reference to higher confidence."""
        if self == LearningStatus.ACTIVE:
            return LearningStatus.PROMOTED
        return self
    
    def demote(self) -> "LearningStatus":
        """Demote a cross-reference to lower confidence."""
        if self == LearningStatus.PROMOTED:
            return LearningStatus.ARCHIVED
        elif self == LearningStatus.ACTIVE:
            return LearningStatus.DEMOTED
        return self


# Display name mappings for UI rendering
ENUM_DISPLAY_NAMES: Dict[Any, str] = {
    InvoiceStatus.DRAFT: "Draft",
    InvoiceStatus.RECEIVED: "Received",
    InvoiceStatus.VALIDATED: "Validated",
    InvoiceStatus.MATCHING: "Matching",
    InvoiceStatus.MATCHED: "Matched",
    InvoiceStatus.EXCEPTION: "Exception",
    InvoiceStatus.APPROVED: "Approved",
    InvoiceStatus.REJECTED: "Rejected",
    InvoiceStatus.PAID: "Paid",
    InvoiceStatus.CANCELLED: "Cancelled",
    MatchDecision.AUTO_APPROVED: "Auto Approved",
    MatchDecision.ONE_CLICK_REVIEW: "1-Click Review",
    MatchDecision.EXCEPTION: "Exception",
    MatchDecision.REJECTED: "Rejected",
    MatchDecision.MANUAL_REVIEW: "Manual Review",
    MatchDecision.NO_MATCH: "No Match",
    ExceptionStatus.OPEN: "Open",
    ExceptionStatus.IN_REVIEW: "In Review",
    ExceptionStatus.RESOLVED: "Resolved",
    ExceptionStatus.DISMISSED: "Dismissed",
    ExceptionStatus.ESCALATED: "Escalated",
}


def get_display_name(enum_value: Any) -> str:
    """Get display name for an enum value.
    
    Args:
        enum_value: Any enum member.
    
    Returns:
        Human-readable display name.
    """
    return ENUM_DISPLAY_NAMES.get(enum_value, enum_value.value.replace("_", " ").title())
