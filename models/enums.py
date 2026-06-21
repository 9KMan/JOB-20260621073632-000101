# models/enums.py
"""SQLAlchemy enums for status and type fields."""

import uuid
from enum import Enum
from typing import Any

from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID


class EnumMixin:
    """Mixin to add common enum functionality."""

    def to_dict(self) -> dict[str, Any]:
        """Convert enum to dictionary."""
        return {
            "value": self.value,
            "name": self.name,
        }

    @classmethod
    def values(cls) -> list[str]:
        """Get all enum values as list."""
        return [e.value for e in cls]


# Invoice Status
class InvoiceStatus(str, Enum, EnumMixin):
    """Status values for invoices."""

    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


# Purchase Order Status
class PurchaseOrderStatus(str, Enum, EnumMixin):
    """Status values for purchase orders."""

    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Delivery Note Status
class DeliveryNoteStatus(str, Enum, EnumMixin):
    """Status values for delivery notes."""

    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


# Match Status
class MatchStatus(str, Enum, EnumMixin):
    """Status values for matching process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_MATCH = "no_match"
    MANUAL_REVIEW = "manual_review"


# Match Decision
class MatchDecision(str, Enum, EnumMixin):
    """Match decision outcomes."""

    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"
    NO_MATCH_FOUND = "no_match_found"


# Exception Type
class ExceptionType(str, Enum, EnumMixin):
    """Types of exceptions in matching."""

    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY_NOTE = "missing_delivery_note"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"
    TAX_VARIANCE = "tax_variance"
    CURRENCY_MISMATCH = "currency_mismatch"
    UNEXPECTED_LINE = "unexpected_line"


# Exception Status
class ExceptionStatus(str, Enum, EnumMixin):
    """Status of exceptions."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


# Source System
class SourceSystem(str, Enum, EnumMixin):
    """Source systems for documents."""

    ERP = "erp"
    OCR = "ocr"
    MANUAL = "manual"
    EDI = "edi"
    API = "api"
    PORTAL = "portal"


# SQLAlchemy column types for enums
def get_invoice_status_enum() -> Any:
    """Get SQLAlchemy enum type for InvoiceStatus."""
    return SQLEnum(InvoiceStatus, name="invoice_status", create_constraint=True)


def get_purchase_order_status_enum() -> Any:
    """Get SQLAlchemy enum type for PurchaseOrderStatus."""
    return SQLEnum(PurchaseOrderStatus, name="purchase_order_status", create_constraint=True)


def get_delivery_note_status_enum() -> Any:
    """Get SQLAlchemy enum type for DeliveryNoteStatus."""
    return SQLEnum(DeliveryNoteStatus, name="delivery_note_status", create_constraint=True)


def get_match_status_enum() -> Any:
    """Get SQLAlchemy enum type for MatchStatus."""
    return SQLEnum(MatchStatus, name="match_status", create_constraint=True)


def get_match_decision_enum() -> Any:
    """Get SQLAlchemy enum type for MatchDecision."""
    return SQLEnum(MatchDecision, name="match_decision", create_constraint=True)


def get_exception_type_enum() -> Any:
    """Get SQLAlchemy enum type for ExceptionType."""
    return SQLEnum(ExceptionType, name="exception_type", create_constraint=True)


def get_exception_status_enum() -> Any:
    """Get SQLAlchemy enum type for ExceptionStatus."""
    return SQLEnum(ExceptionStatus, name="exception_status", create_constraint=True)


def get_source_system_enum() -> Any:
    """Get SQLAlchemy enum type for SourceSystem."""
    return SQLEnum(SourceSystem, name="source_system", create_constraint=True)
