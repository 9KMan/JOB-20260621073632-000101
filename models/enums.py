# models/enums.py
"""SQLAlchemy enum types and Pydantic enums.

Defines all status enums used throughout the application.
"""

import uuid
from enum import Enum

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR


class UUIDType(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise CHAR(36).
    """
    
    impl = CHAR
    cache_ok = True
    
    def __init__(self) -> None:
        super().__init__(36)
    
    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value
        return value
    
    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value


# Invoice Status Enum
class InvoiceStatus(str, Enum):
    """Status values for invoices."""
    
    DRAFT = "draft"
    PENDING = "pending"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


# Purchase Order Status Enum
class PurchaseOrderStatus(str, Enum):
    """Status values for purchase orders."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# Delivery Note Status Enum
class DeliveryNoteStatus(str, Enum):
    """Status values for delivery notes."""
    
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    FULLY_INVOICED = "fully_invoiced"
    CANCELLED = "cancelled"


# Matching Status Enum
class MatchStatus(str, Enum):
    """Status values for match records."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"


# Match Decision Enum
class MatchDecision(str, Enum):
    """Match decision outcomes."""
    
    AUTO_APPROVED = "auto_approved"  # Score >= THRESHOLD_HIGH
    MANUAL_APPROVED = "manual_approved"  # Score >= THRESHOLD_MID, approved by user
    EXCEPTION = "exception"  # Score >= THRESHOLD_LOW, needs investigation
    REJECTED = "rejected"  # Score < THRESHOLD_LOW
    DISMISSED = "dismissed"  # User explicitly dismissed


# Line Status Enum
class LineStatus(str, Enum):
    """Status values for individual lines."""
    
    OPEN = "open"
    PARTIAL = "partial"
    FULLY_MATCHED = "fully_matched"
    OVER_DELIVERED = "over_delivered"
    UNDER_DELIVERED = "under_delivered"
    DISPUTED = "disputed"
    CLOSED = "closed"


# Exception Type Enum
class ExceptionType(str, Enum):
    """Types of matching exceptions."""
    
    PRICE_VARIANCE = "price_variance"
    QUANTITY_VARIANCE = "quantity_variance"
    MISSING_PO = "missing_po"
    MISSING_INVOICE = "missing_invoice"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MULTIPLE_MATCHES = "multiple_matches"
    NO_MATCH_FOUND = "no_match_found"
    DATE_VARIANCE = "date_variance"
    VENDOR_MISMATCH = "vendor_mismatch"


# Exception Resolution Enum
class ExceptionResolution(str, Enum):
    """Ways to resolve exceptions."""
    
    PENDING = "pending"
    APPROVED_WITH_VARIANCE = "approved_with_variance"
    MANUAL_MATCH = "manual_match"
    WRITE_OFF = "write_off"
    HELD_FOR_REVIEW = "held_for_review"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


# Ledger Entry Type
class LedgerEntryType(str, Enum):
    """Types of balance ledger entries."""
    
    INVOICE = "invoice"
    DELIVERY = "delivery"
    CREDIT = "credit"
    ADJUSTMENT = "adjustment"
    PAYMENT = "payment"


# Match Confidence Level
class MatchConfidence(str, Enum):
    """Confidence levels for learned matches."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
