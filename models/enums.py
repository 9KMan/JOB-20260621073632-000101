# models/enums.py
"""Enumeration types used across the AP automation engine."""

import enum


class InvoiceStatus(str, enum.Enum):
    """Lifecycle status of an invoice record."""

    DRAFT = "draft"
    RECEIVED = "received"
    MATCHING_IN_PROGRESS = "matching_in_progress"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, enum.Enum):
    """Lifecycle status of a purchase order."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryNoteStatus(str, enum.Enum):
    """Lifecycle status of a delivery note."""

    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class MatchingDecision(str, enum.Enum):
    """
    Outcome of the matching engine for a given invoice / PO pair.

    Values are ordered from most confident to least confident.
    """

    AUTO_APPROVED = "auto_approved"
    """Score >= THRESHOLD_HIGH — fully confident, auto-approved."""

    ONE_CLICK_REVIEW = "one_click_review"
    """Score between THRESHOLD_MID and THRESHOLD_HIGH — needs human confirmation."""

    EXCEPTION = "exception"
    """Score between THRESHOLD_LOW and THRESHOLD_MID — flagged for exception handling."""

    REJECTED = "rejected"
    """Score < THRESHOLD_LOW — no viable match found."""


class ExceptionType(str, enum.Enum):
    """Categorises a matching exception for triage."""

    PRICE_MISMATCH = "price_mismatch"
    """Unit price differs beyond tolerance."""

    QUANTITY_MISMATCH = "quantity_mismatch"
    """Billed quantity differs beyond tolerance."""

    MISSING_PO = "missing_po"
    """No PO anchor found for this invoice."""

    MISSING_DELIVERY = "missing_delivery"
    """No delivery note found for this PO line."""

    DUPLICATE_INVOICE = "duplicate_invoice"
    """Potential duplicate of an existing invoice."""

    OVER_INVOICED = "over_invoiced"
    """Invoice amount exceeds PO line value."""

    PARTIAL_DELIVERY = "partial_delivery"
    """PO line quantity exceeds delivered quantity."""

    CROSS_REF_BLOCKED = "cross_ref_blocked"
    """Cross-reference record conflicts with current match."""


class LineStatus(str, enum.Enum):
    """Status of an individual line item within a document."""

    OPEN = "open"
    """Line has remaining quantity to be matched."""

    PARTIALLY_MATCHED = "partially_matched"
    """Line has been partially matched."""

    FULLY_MATCHED = "fully_matched"
    """Line has been fully matched."""

    OVER_DELIVERED = "over_delivered"
    """Delivered quantity exceeds ordered quantity."""

    OVER_INVOICED = "over_invoiced"
    """Invoiced quantity exceeds delivered quantity."""

    CANCELLED = "cancelled"
