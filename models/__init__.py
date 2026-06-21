// models/__init__.py
"""Database models package.

This package contains all SQLAlchemy ORM models for the AP Automation Engine.
Models are organized by domain:
- base: Declarative base and mixins
- enums: Status and type enumerations
- invoice: Invoice-related models
- purchase_order: Purchase order models
- delivery_note: Delivery note models
- balance_ledger: Balance tracking models
- cross_ref: Learning loop / cross-reference models
"""

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import (
    InvoiceStatus,
    PurchaseOrderStatus,
    DeliveryNoteStatus,
    MatchingStatus,
    DecisionType,
    MatchConfidence,
    ExceptionStatus,
)
from models.invoice import (
    Invoice,
    InvoiceLine,
    InvoiceLineItem,
)
from models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderLine,
)
from models.delivery_note import (
    DeliveryNote,
    DeliveryNoteLine,
)
from models.balance_ledger import (
    BalanceLedger,
    LedgerEntryType,
)
from models.cross_ref import (
    CrossRef,
    CrossRefType,
    MatchHistory,
)

__all__ = [
    # Base and mixins
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    # Enums
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchingStatus",
    "DecisionType",
    "MatchConfidence",
    "ExceptionStatus",
    # Invoice models
    "Invoice",
    "InvoiceLine",
    "InvoiceLineItem",
    # Purchase order models
    "PurchaseOrder",
    "PurchaseOrderLine",
    # Delivery note models
    "DeliveryNote",
    "DeliveryNoteLine",
    # Balance ledger models
    "BalanceLedger",
    "LedgerEntryType",
    # Cross reference models
    "CrossRef",
    "CrossRefType",
    "MatchHistory",
]
