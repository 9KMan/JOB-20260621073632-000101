// models/enums.py
"""Enumeration types for the AP Automation Engine.

This module defines all status and type enumerations used
throughout the application for type safety and data validation.
"""

import enum
from typing import TYPE_CHECKING


class InvoiceStatus(str, enum.Enum):
    """Status of an invoice in the system.

    Attributes:
        DRAFT: Invoice is being created/edited.
        SUBMITTED: Invoice has been submitted for processing.
        PENDING_MATCHING: Invoice is pending matching against PO/delivery.
        MATCHED: Invoice has been successfully matched.
        PARTIALLY_MATCHED: Invoice is partially matched.
        EXCEPTION: Invoice has matching exceptions.
        APPROVED: Invoice has been approved for payment.
        REJECTED: Invoice has been rejected.
        PAID: Invoice has been paid.
        CANCELLED: Invoice has been cancelled.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_MATCHING = "pending_matching"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Status of a purchase order.

    Attributes:
        DRAFT: PO is being prepared.
        SENT: PO has been sent to supplier.
        CONFIRMED: PO has been confirmed by supplier.
        PARTIAL_RECEIPT: Some items have been received.
        RECEIVED: All items have been received.
        CLOSED: PO is closed (completed or cancelled).
        CANCELLED: PO has been cancelled.
    """

    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIAL_RECEIPT = "partial_receipt"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Status of a delivery note.

    Attributes:
        DRAFT: Delivery note is being created.
        CONFIRMED: Delivery has been confirmed.
        PARTIALLY_PROCESSED: Some lines have been processed.
        PROCESSED: All lines have been processed.
        CANCELLED: Delivery note has been cancelled.
    """

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_PROCESSED = "partially_processed"
    PROCESSED = "processed"
    CANCELLED = "cancelled"


class MatchingStatus(str, enum.Enum):
    """Status of the matching process.

    Attributes:
        PENDING: Matching has not started.
        IN_PROGRESS: Matching is currently running.
        COMPLETED: Matching completed successfully.
        FAILED: Matching failed with an error.
        CANCELLED: Matching was cancelled.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DecisionType(str, enum.Enum):
    """Type of matching decision.

    Attributes:
        AUTO_APPROVED: Invoice auto-approved based on high confidence score.
        MANUAL_REVIEW: Invoice requires 1-click manual review.
        EXCEPTION: Invoice has exceptions requiring detailed review.
        REJECTED: Invoice rejected due to low confidence or business rules.
        PENDING: Decision pending (no matching possible yet).
    """

    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    PENDING = "pending"


class MatchConfidence(str, enum.Enum):
    """Confidence level of a match.

    Attributes:
        HIGH: High confidence match (>threshold_high).
        MEDIUM: Medium confidence match (threshold_mid to threshold_high).
        LOW: Low confidence match (threshold_low to threshold_mid).
        VERY_LOW: Very low confidence match (<threshold_low).
        NONE: No match found.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    NONE = "none"


class ExceptionStatus(str, enum.Enum):
    """Status of a matching exception.

    Attributes:
        OPEN: Exception is open and needs attention.
        IN_REVIEW: Exception is being reviewed.
        RESOLVED: Exception has been resolved.
        DISMISSED: Exception has been dismissed.
        ESCALATED: Exception has been escalated.
    """

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class LedgerEntryType(str, enum.Enum):
    """Type of balance ledger entry.

    Attributes:
        INVOICE: Invoice amount entry.
        DELIVERY: Delivery amount entry.
        CREDIT: Credit memo entry.
        DEBIT: Debit memo entry.
        ADJUSTMENT: Manual adjustment entry.
        WRITE_OFF: Write-off entry.
    """

    INVOICE = "invoice"
    DELIVERY = "delivery"
    CREDIT = "credit"
    DEBIT = "debit"
    ADJUSTMENT = "adjustment"
    WRITE_OFF = "write_off"


class CrossRefType(str, enum.Enum):
    """Type of cross-reference record.

    Attributes:
        SUPPLIER_MATCH: Supplier-level match confirmation.
        PRODUCT_MATCH: Product/item-level match confirmation.
        PRICE_MATCH: Price-level match confirmation.
        QTY_MATCH: Quantity-level match confirmation.
    """

    SUPPLIER_MATCH = "supplier_match"
    PRODUCT_MATCH = "product_match"
    PRICE_MATCH = "price_match"
    QTY_MATCH = "qty_match"


# Re-export enums for convenience
__all__ = [
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchingStatus",
    "DecisionType",
    "MatchConfidence",
    "ExceptionStatus",
    "LedgerEntryType",
    "CrossRefType",
]
