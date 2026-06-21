# models/enums.py
"""Enumeration types for AP Automation models.

These enums define the allowed values for various status and type fields
across all database models.
"""

import uuid
from enum import Enum

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DocumentStatus(str, Enum):
    """Base document status enum."""

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class InvoiceStatus(str, Enum):
    """Invoice processing status."""

    RECEIVED = "received"
    VALIDATED = "validated"
    MATCHING = "matching"
    MATCHED = "matched"
    EXCEPTION = "exception"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status."""

    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class DeliveryNoteStatus(str, Enum):
    """Delivery note status."""

    CREATED = "created"
    SENT = "sent"
    RECEIVED = "received"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    """Matching status for invoice-PO line relationships."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    EXCEPTION = "exception"
    OVERMATCHED = "overmatched"


class MatchConfidence(str, Enum):
    """Confidence level for match decisions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class DecisionType(str, Enum):
    """Type of matching decision made by the engine."""

    AUTO_APPROVED = "auto_approved"
    MANUAL_REVIEW = "manual_review"
    EXCEPTION = "exception"
    REJECTED = "rejected"


class ExceptionStatus(str, Enum):
    """Status of matching exceptions."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class ExceptionReason(str, Enum):
    """Reason codes for matching exceptions."""

    PRICE_MISMATCH = "price_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    MISSING_PO = "missing_po"
    MISSING_DELIVERY = "missing_delivery"
    DUPLICATE_INVOICE = "duplicate_invoice"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    TAX_MISMATCH = "tax_mismatch"
    DATE_MISMATCH = "date_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    SUPPLIER_MISMATCH = "supplier_mismatch"
    OTHER = "other"


class LineType(str, Enum):
    """Type of line item."""

    STANDARD = "standard"
    SERVICE = "service"
    MISCELLANEOUS = "miscellaneous"
    DISCOUNT = "discount"
    TAX = "tax"
    SHIPPING = "shipping"


class PaymentStatus(str, Enum):
    """Payment processing status."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CurrencyCode(str, Enum):
    """ISO 4217 currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    JPY = "JPY"
    CNY = "CNY"
    AUD = "AUD"
    CAD = "CAD"
    SEK = "SEK"
    NOK = "NOK"
    DKK = "DKK"
    PLN = "PLN"
    CZK = "CZK"
    HUF = "HUF"
    RON = "RON"
    BGN = "BGN"
    HRK = "HRK"
    RUB = "RUB"
    TRY = "TRY"
    ZAR = "ZAR"


class TaxType(str, Enum):
    """Tax type classification."""

    VAT = "vat"
    GST = "gst"
    SALES_TAX = "sales_tax"
    SERVICE_TAX = "service_tax"
    WITHHOLDING_TAX = "withholding_tax"
    EXEMPT = "exempt"
    ZERO_RATED = "zero_rated"
    OUT_OF_SCOPE = "out_of_scope"
