# src/app/models/enums.py
"""Enumeration types for the application."""
from enum import Enum


class DocumentStatus(str, Enum):
    """Status for documents (PO, Invoice, Delivery Note)."""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    RECEIVED = "RECEIVED"
    DISPUTED = "DISPUTED"


class LineStatus(str, Enum):
    """Status for document lines."""
    PENDING = "PENDING"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    DISPUTED = "DISPUTED"
    CLOSED = "CLOSED"


class MatchStatus(str, Enum):
    """Status for match results."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class MatchResultType(str, Enum):
    """Type of match result."""
    FULL_3_WAY = "FULL_3_WAY"  # Invoice, DN, and PO all matched
    INVOICE_DN = "INVOICE_DN"  # Invoice matched with DN only
    INVOICE_PO = "INVOICE_PO"  # Invoice matched with PO only
    DN_PO = "DN_PO"  # DN matched with PO only
    UNMATCHED = "UNMATCHED"  # No matches found
    OVERMATCHED = "OVERMATCHED"  # Multiple potential matches


class DecisionType(str, Enum):
    """Type of human review decision."""
    APPROVE = "APPROVE"  # Confirm the match
    REJECT = "REJECT"  # Reject the match
    MODIFY = "MODIFY"  # Modify and re-evaluate
    ESCALATE = "ESCALATE"  # Escalate to higher authority
    SPLIT = "SPLIT"  # Split into multiple matches


class BalanceType(str, Enum):
    """Type of balance in the ledger."""
    OPEN = "OPEN"  # Original amount
    UTILIZED = "UTILIZED"  # Used in matching
    REMAINING = "REMAINING"  # Remaining after matching
    VARIANCE = "VARIANCE"  # Difference/variance
    WRITE_OFF = "WRITE_OFF"  # Written off amount
