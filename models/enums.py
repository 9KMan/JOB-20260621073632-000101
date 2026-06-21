// models/enums.py
"""SQLAlchemy and Pydantic enums for AP Automation Engine.

Defines all status enums, decision types, and related constants.
"""

import enum
from typing import Annotated

from pydantic import Field


class DocumentStatus(str, enum.Enum):
    """Status for invoices, POs, and delivery notes."""

    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXCEPTION = "exception"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class MatchStatus(str, enum.Enum):
    """Status of the matching process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class MatchDecision(str, enum.Enum):
    """Matching decision outcome."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_APPROVE = "one_click_approve"
    ONE_CLICK_REJECT = "one_click_reject"
    EXCEPTION = "exception"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


class MatchingScore(float, enum.Enum):
    """Matching score categories."""

    EXACT = 100.0
    HIGH = 90.0
    GOOD = 80.0
    ACCEPTABLE = 70.0
    LOW = 50.0
    POOR = 30.0
    FAILED = 0.0


class ExceptionType(str, enum.Enum):
    """Types of matching exceptions."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    DATE_VARIANCE = "date_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    MULTIPLE_PO_MATCH = "multiple_po_match"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    OTHER = "other"


class ExceptionReason(str, enum.Enum):
    """Detailed reasons for exceptions."""

    PO_PRICE_MISMATCH = "po_price_mismatch"
    INVOICE_PRICE_MISMATCH = "invoice_price_mismatch"
    QUANTITY_EXCEEDS_PO = "quantity_exceeds_po"
    QUANTITY_EXCEEDS_DELIVERY = "quantity_exceeds_delivery"
    DELIVERY_DATE_OUTSIDE_TOLERANCE = "delivery_date_outside_tolerance"
    INVOICE_DATE_BEFORE_PO = "invoice_date_before_po"
    UNABLE_TO_ANCHOR_PO = "unable_to_anchor_po"
    MULTIPLE_POS_POSSIBLE = "multiple_pos_possible"
    NO_MATCHING_DELIVERY = "no_matching_delivery"
    INVOICE_ALREADY_EXISTS = "invoice_already_exists"
    BLOCKED_INVOICE = "blocked_invoice"
    OTHER_REASON = "other_reason"


class ExceptionStatus(str, enum.Enum):
    """Status of an exception in the queue."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class SupplierConfidence(str, enum.Enum):
    """Confidence level for supplier matching."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


# Pydantic enum annotations for API schemas
DocumentStatusEnum = Annotated[DocumentStatus, Field(description="Document status")]
MatchStatusEnum = Annotated[MatchStatus, Field(description="Matching status")]
MatchDecisionEnum = Annotated[MatchDecision, Field(description="Match decision")]
MatchingScoreEnum = Annotated[MatchingScore, Field(description="Matching score category")]
ExceptionTypeEnum = Annotated[ExceptionType, Field(description="Exception type")]
ExceptionReasonEnum = Annotated[ExceptionReason, Field(description="Exception reason")]
ExceptionStatusEnum = Annotated[ExceptionStatus, Field(description="Exception status")]
SupplierConfidenceEnum = Annotated[SupplierConfidence, Field(description="Supplier confidence")]
