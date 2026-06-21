# models/enums.py
# Status enums and decision types
# AP Automation Core Engine — FinaRo

"""SQLAlchemy enum types for status fields and decision types.

Uses PostgreSQL ENUM types for type safety and database-level constraints.
"""

from enum import Enum

from sqlalchemy import Enum as SQLEnum


class InvoiceStatus(str, Enum):
    """Invoice status enumeration.

    Attributes:
        DRAFT: Invoice is in draft state, not yet submitted.
        SUBMITTED: Invoice has been submitted for processing.
        PENDING_MATCHING: Invoice is awaiting matching engine processing.
        MATCHING_IN_PROGRESS: Matching engine is currently processing the invoice.
        MATCHED: Invoice has been matched to PO and/or delivery note.
        PARTIALLY_MATCHED: Invoice has been partially matched.
        EXCEPTION: Invoice has matching exceptions requiring review.
        APPROVED: Invoice has been approved for payment.
        REJECTED: Invoice has been rejected.
        PAID: Invoice has been paid.
        CANCELLED: Invoice has been cancelled.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_MATCHING = "pending_matching"
    MATCHING_IN_PROGRESS = "matching_in_progress"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status enumeration.

    Attributes:
        DRAFT: PO is in draft state.
        ISSUED: PO has been issued to vendor.
        PARTIALLY_RECEIVED: Some goods have been received.
        RECEIVED: All goods have been received.
        CLOSED: PO has been closed.
        CANCELLED: PO has been cancelled.
    """

    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status enumeration.

    Attributes:
        DRAFT: Delivery note is in draft state.
        CONFIRMED: Delivery note has been confirmed.
        PARTIALLY_INVOICED: Some items have been invoiced.
        INVOICED: All items have been invoiced.
        CANCELLED: Delivery note has been cancelled.
    """

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_INVOICED = "partially_invoiced"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class MatchingDecision(str, Enum):
    """Matching engine decision enumeration.

    Attributes:
        AUTO_APPROVED: High confidence match, auto-approved.
        REVIEW_APPROVED: Medium confidence, approved after review.
        REVIEW_REJECTED: Medium confidence, rejected after review.
        EXCEPTION: Low confidence, requires exception handling.
        NO_MATCH: Unable to find matching records.
        MANUAL_REQUIRED: Manual matching required.
    """

    AUTO_APPROVED = "auto_approved"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    EXCEPTION = "exception"
    NO_MATCH = "no_match"
    MANUAL_REQUIRED = "manual_required"


class ExceptionType(str, Enum):
    """Matching exception type enumeration.

    Attributes:
        PRICE_VARIANCE: Price doesn't match within tolerance.
        QUANTITY_VARIANCE: Quantity doesn't match within tolerance.
        MISSING_PO: PO reference is missing or invalid.
        MISSING_DELIVERY: Delivery note reference is missing or invalid.
        DUPLICATE_INVOICE: Potential duplicate invoice detected.
        MULTIPLE_MATCHES: Multiple potential matches found.
        DATE_VARIANCE: Date mismatch detected.
        VENDOR_MISMATCH: Vendor doesn't match across documents.
    """

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MULTIPLE_MATCHES = "multiple_matches"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"


class ExceptionStatus(str, Enum):
    """Exception status enumeration.

    Attributes:
        OPEN: Exception is open and awaiting resolution.
        UNDER_REVIEW: Exception is being reviewed.
        RESOLVED: Exception has been resolved.
        DISMISSED: Exception has been dismissed.
        ESCALATED: Exception has been escalated.
    """

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LineStatus(str, Enum):
    """Line item status enumeration.

    Attributes:
        PENDING: Line item is pending.
        MATCHED: Line item has been matched.
        PARTIALLY_MATCHED: Line item has been partially matched.
        EXCEPTION: Line item has exceptions.
    """

    PENDING = "pending"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"


class BalanceType(str, Enum):
    """Balance ledger transaction type.

    Attributes:
        PO_INITIAL: Initial PO balance created.
        PO_CANCELLED: PO cancelled, balance released.
        DELIVERY_RECEIVED: Goods received, reduces PO balance.
        INVOICE_MATCHED: Invoice matched, reduces available balance.
        CREDIT_MEMO: Credit memo applied.
        ADJUSTMENT: Manual adjustment.
    """

    PO_INITIAL = "po_initial"
    PO_CANCELLED = "po_cancelled"
    DELIVERY_RECEIVED = "delivery_received"
    INVOICE_MATCHED = "invoice_matched"
    CREDIT_MEMO = "credit_memo"
    ADJUSTMENT = "adjustment"


class MatchConfidence(str, Enum):
    """Match confidence level from learning system.

    Attributes:
        HIGH: High confidence match (>90%).
        MEDIUM: Medium confidence match (70-90%).
        LOW: Low confidence match (50-70%).
        UNCERTAIN: Uncertain match (<50%).
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class LearningStatus(str, Enum):
    """Learning loop status for cross-reference records.

    Attributes:
        ACTIVE: Cross-reference is active and being used.
        PROMOTED: Cross-reference has been promoted to confirmed.
        DEMOTED: Cross-reference has been demoted.
        ARCHIVED: Cross-reference has been archived.
    """

    ACTIVE = "active"
    PROMOTED = "promoted"
    DEMOTED = "demoted"
    ARCHIVED = "archived"


# SQLAlchemy enum types for use in column definitions
InvoiceStatusType = SQLEnum(
    InvoiceStatus,
    name="invoice_status",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

PurchaseOrderStatusType = SQLEnum(
    PurchaseOrderStatus,
    name="purchase_order_status",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

DeliveryNoteStatusType = SQLEnum(
    DeliveryNoteStatus,
    name="delivery_note_status",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

MatchingDecisionType = SQLEnum(
    MatchingDecision,
    name="matching_decision",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

ExceptionTypeSQL = SQLEnum(
    ExceptionType,
    name="exception_type",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

ExceptionStatusType = SQLEnum(
    ExceptionStatus,
    name="exception_status",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

LineStatusType = SQLEnum(
    LineStatus,
    name="line_status",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

BalanceTypeSQL = SQLEnum(
    BalanceType,
    name="balance_type",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

MatchConfidenceType = SQLEnum(
    MatchConfidence,
    name="match_confidence",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)

LearningStatusType = SQLEnum(
    LearningStatus,
    name="learning_status",
    create_constraint=True,
    create_type=True,
    values_callable=lambda x: [e.value for e in x],
)
