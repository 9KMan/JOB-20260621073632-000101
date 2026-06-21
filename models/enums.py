# models/enums.py
"""
Status enums, decision types, and domain constants.

Using SQLAlchemy native Enum types for database storage
and Python Enum classes for code clarity.
"""

from __future__ import annotations

from enum import Enum


class InvoiceStatus(str, Enum):
    """
    Invoice lifecycle status.
    
    DRAFT -> PENDING_MATCHING -> MATCHING_IN_PROGRESS -> 
    MATCHED -> EXCEPTION -> APPROVED -> REJECTED -> PAID
    """

    DRAFT = "draft"
    PENDING_MATCHING = "pending_matching"
    MATCHING_IN_PROGRESS = "matching_in_progress"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

    @classmethod
    def active_statuses(cls) -> list["InvoiceStatus"]:
        """Return statuses that represent an active (non-terminal) invoice."""
        return [
            cls.DRAFT,
            cls.PENDING_MATCHING,
            cls.MATCHING_IN_PROGRESS,
            cls.MATCHED,
            cls.EXCEPTION,
        ]

    @classmethod
    def terminal_statuses(cls) -> list["InvoiceStatus"]:
        """Return statuses that represent a terminal state."""
        return [
            cls.APPROVED,
            cls.REJECTED,
            cls.PAID,
        ]

    @classmethod
    def matching_final_states(cls) -> list["InvoiceStatus"]:
        """Statuses an invoice can reach after matching."""
        return [
            cls.MATCHED,
            cls.EXCEPTION,
        ]


class POStatus(str, Enum):
    """
    Purchase Order lifecycle status.
    
    DRAFT -> PENDING_APPROVAL -> APPROVED -> PARTIALLY_INVOICED -> 
    FULLY_INVOICED -> CLOSED -> CANCELLED
    """

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PARTIALLY_INVOICED = "partially_invoiced"
    FULLY_INVOICED = "fully_invoiced"
    CLOSED = "closed"
    CANCELLED = "cancelled"

    @classmethod
    def active_statuses(cls) -> list["POStatus"]:
        """Return statuses that represent an active PO."""
        return [
            cls.DRAFT,
            cls.PENDING_APPROVAL,
            cls.APPROVED,
            cls.PARTIALLY_INVOICED,
        ]

    @classmethod
    def open_statuses(cls) -> list["POStatus"]:
        """Return statuses that allow invoice matching."""
        return [
            cls.APPROVED,
            cls.PARTIALLY_INVOICED,
        ]


class DeliveryNoteStatus(str, Enum):
    """
    Delivery Note status.
    
    RECEIVED -> PARTIALLY_MATCHED -> FULLY_MATCHED -> CANCELLED
    """

    RECEIVED = "received"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


class MatchDecision(str, Enum):
    """
    Final matching decision for an invoice-PO match.
    
    AUTO_APPROVED: Score >= THRESHOLD_HIGH -> Auto-approved
    ONE_CLICK_REVIEW: Score >= THRESHOLD_MID -> Approve/reject in one click
    EXCEPTION: Score >= THRESHOLD_LOW -> Manual review required
    REJECTED: Score < THRESHOLD_LOW -> Automatically rejected
    """

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PENDING = "pending"

    @classmethod
    def from_score(cls, score: float, high: float, mid: float, low: float) -> "MatchDecision":
        """
        Determine decision based on matching score and thresholds.
        
        Args:
            score: Matching score (0-100)
            high: Auto-approve threshold
            mid: One-click review threshold  
            low: Exception threshold
            
        Returns:
            Appropriate MatchDecision
        """
        if score >= high:
            return cls.AUTO_APPROVED
        elif score >= mid:
            return cls.ONE_CLICK_REVIEW
        elif score >= low:
            return cls.EXCEPTION
        else:
            return cls.REJECTED


class MatchStatus(str, Enum):
    """Status of an individual line match record."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class ExceptionType(str, Enum):
    """
    Types of matching exceptions that require manual review.
    
    PRICE_VARIANCE: Invoice price differs from PO price beyond tolerance
    QTY_VARIANCE: Invoice quantity differs from PO quantity beyond tolerance
    MISSING_PO: No matching PO found for invoice
    MULTIPLE_MATCHES: Invoice matches multiple POs (ambiguous)
    DUPLICATE_INVOICE: Potential duplicate invoice detected
    PARTIAL_MATCH: Only some invoice lines matched to PO
    BALANCE_EXCEEDED: Invoice amount exceeds available PO balance
    LEARNING_CONFLICT: Learning loop conflicting decision
    """

    PRICE_VARIANCE = "price_variance"
    QTY_VARIANCE = "qty_variance"
    MISSING_PO = "missing_po"
    MULTIPLE_MATCHES = "multiple_matches"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    BALANCE_EXCEEDED = "balance_exceeded"
    LEARNING_CONFLICT = "learning_conflict"


class ExceptionResolution(str, Enum):
    """
    How an exception was resolved.
    
    AUTO_APPROVED: Automatically approved after review
    MANUAL_APPROVED: Manually approved by user
    REJECTED: Rejected
    DISMISSED: Dismissed (not a real exception)
    SPLIT_APPROVAL: Partially approved, partially rejected
    ESCALATED: Escalated to higher authority
    """

    AUTO_APPROVED = "auto_approved"
    MANUAL_APPROVED = "manual_approved"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    SPLIT_APPROVAL = "split_approval"
    ESCALATED = "escalated"
