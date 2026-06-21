// models/enums.py
"""SQLAlchemy and Pydantic enums for AP Automation.

This module defines all enumeration types used throughout the system
for status tracking, decision types, and exception handling.
"""

import enum


class DocumentStatus(str, enum.Enum):
    """Status for documents (Invoice, PO, Delivery Note).

    Values:
        DRAFT: Document is in draft state
        PENDING: Document is pending processing
        MATCHED: Document has been matched
        APPROVED: Document has been approved
        REJECTED: Document has been rejected
        EXCEPTION: Document has an exception requiring review
        CANCELLED: Document has been cancelled
        ARCHIVED: Document has been archived
    """

    DRAFT = "draft"
    PENDING = "pending"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class MatchStatus(str, enum.Enum):
    """Status of matching process for a document.

    Values:
        PENDING: Match not yet attempted
        IN_PROGRESS: Match is currently running
        FULL_MATCH: Perfect match found
        PARTIAL_MATCH: Partial match with exceptions
        NO_MATCH: No matching document found
        MULTIPLE_MATCHES: Multiple potential matches found
        ANCHORED: Document anchored to PO
        LINES_MATCHED: Line-level matching complete
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    MULTIPLE_MATCHES = "multiple_matches"
    ANCHORED = "anchored"
    LINES_MATCHED = "lines_matched"


class DecisionType(str, enum.Enum):
    """Final decision type from matching engine.

    Values:
        AUTO_APPROVED: Automatically approved (score >= HIGH threshold)
        ONE_CLICK_APPROVE: Ready for one-click approval (score >= MID threshold)
        MANUAL_REVIEW: Requires manual review (score >= LOW threshold)
        EXCEPTION: Has exceptions requiring resolution
        REJECTED: Rejected due to low score or business rules
    """

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class ExceptionReason(str, enum.Enum):
    """Reason codes for matching exceptions.

    Values:
        PRICE_VARIANCE: Price doesn't match within tolerance
        QUANTITY_VARIANCE: Quantity doesn't match within tolerance
        MISSING_LINE: Invoice line has no matching PO line
        DUPLICATE_INVOICE: Potential duplicate invoice detected
        MULTIPLE_POS: Multiple POs match same invoice
        VENDOR_MISMATCH: Vendor doesn't match between documents
        DATE_OUT_OF_RANGE: Delivery date outside PO validity period
        OVER_DELIVERED: Delivered quantity exceeds ordered quantity
        UNDER_DELIVERED: Delivered quantity less than ordered quantity
        AMOUNT_MISMATCH: Total amounts don't match
    """

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_LINE = "missing_line"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MULTIPLE_POS = "multiple_pos"
    VENDOR_MISMATCH = "vendor_mismatch"
    DATE_OUT_OF_RANGE = "date_out_of_range"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"
    AMOUNT_MISMATCH = "amount_mismatch"


class ExceptionStatus(str, enum.Enum):
    """Status of exceptions.

    Values:
        OPEN: Exception is open and needs resolution
        RESOLVED: Exception has been resolved
        DISMISSED: Exception has been dismissed as invalid
        ESCALATED: Exception has been escalated for review
    """

    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class MatchConfidence(str, enum.Enum):
    """Confidence level for matches.

    Values:
        HIGH: High confidence match (>= 90%)
        MEDIUM: Medium confidence match (>= 70%)
        LOW: Low confidence match (>= 50%)
        NONE: No confidence in match
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
