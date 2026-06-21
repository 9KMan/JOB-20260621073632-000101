# models/enums.py
"""Enum definitions for the AP Automation system.

All enums use PostgreSQL native type with checks for data integrity.
"""

import uuid
from enum import Enum

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column


# Invoice Status Enum
class InvoiceStatus(str, Enum):
    """Status values for invoice records."""

    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    APPROVED = "approved"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# Purchase Order Status Enum
class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Delivery Note Status Enum
class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""

    DRAFT = "draft"
    RECEIVED = "received"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CANCELLED = "cancelled"


# Line Item Status Enum
class LineStatus(str, Enum):
    """Status values for line items (PO lines, invoice lines, DN lines)."""

    PENDING = "pending"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    OVER_DELIVERED = "over_delivered"
    CLOSED = "closed"


# Matching Status Enum
class MatchingStatus(str, Enum):
    """Status values for matching operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Matching Decision Enum
class MatchingDecision(str, Enum):
    """Decision outcomes from the matching engine."""

    AUTO_APPROVED = "auto_approved"
    ONE_CLICK_REVIEW = "one_click_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


# Exception Status Enum
class ExceptionStatus(str, Enum):
    """Status values for matching exceptions."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# Exception Reason Enum
class ExceptionReason(str, Enum):
    """Reasons why a match resulted in an exception."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    OVER_INVOICED = "over_invoiced"
    UNDER_INVOICED = "under_invoiced"
    DATE_MISMATCH = "date_mismatch"
    PARTIAL_MATCH = "partial_match"
    MULTIPLE_POSSIBILITIES = "multiple_possibilities"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


# Balance Transaction Type Enum
class BalanceTransactionType(str, Enum):
    """Types of balance ledger transactions."""

    INVOICE_RECEIVED = "invoice_received"
    INVOICE_CANCELLED = "invoice_cancelled"
    DELIVERY_RECEIVED = "delivery_received"
    CREDIT_NOTE = "credit_note"
    PAYMENT = "payment"
    WRITE_OFF = "write_off"
    MANUAL_ADJUSTMENT = "manual_adjustment"


# Cross Reference Status Enum
class CrossRefStatus(str, Enum):
    """Status values for learning cross-references."""

    PENDING = "pending"
    LEARNED = "learned"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    EXPIRED = "expired"


# SQLAlchemy enum columns for use in models
# These are defined as functions to allow reuse across models

def invoice_status_column() -> dict:
    """Return column configuration for invoice status."""
    return {
        "name": "status",
        "type_": PGEnum(
            InvoiceStatus,
            name="invoice_status",
            create_constraint=True,
            preguard=True,
        ),
        "default": InvoiceStatus.DRAFT,
        "nullable": False,
    }


def po_status_column() -> dict:
    """Return column configuration for PO status."""
    return {
        "name": "status",
        "type_": PGEnum(
            PurchaseOrderStatus,
            name="purchase_order_status",
            create_constraint=True,
            preguard=True,
        ),
        "default": PurchaseOrderStatus.DRAFT,
        "nullable": False,
    }


def delivery_note_status_column() -> dict:
    """Return column configuration for delivery note status."""
    return {
        "name": "status",
        "type_": PGEnum(
            DeliveryNoteStatus,
            name="delivery_note_status",
            create_constraint=True,
            preguard=True,
        ),
        "default": DeliveryNoteStatus.DRAFT,
        "nullable": False,
    }


def line_status_column() -> dict:
    """Return column configuration for line status."""
    return {
        "name": "status",
        "type_": PGEnum(
            LineStatus,
            name="line_status",
            create_constraint=True,
            preguard=True,
        ),
        "default": LineStatus.PENDING,
        "nullable": False,
    }
