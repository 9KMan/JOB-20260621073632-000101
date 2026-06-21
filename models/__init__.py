// models/__init__.py
"""Database models package.

This package contains all SQLAlchemy ORM models for the AP Automation Engine.

Models:
    - Invoice: Invoice records from suppliers
    - PurchaseOrder: Purchase orders sent to suppliers
    - DeliveryNote: Delivery notes/confirmation of delivery
    - BalanceLedger: Running balance per PO line
    - CrossRef: Learning/cross-reference table for confirmed matches
"""

from models.base import Base
from models.invoice import Invoice, InvoiceLine
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.balance_ledger import BalanceLedger
from models.cross_ref import CrossRef
from models.enums import (
    InvoiceStatus,
    PurchaseOrderStatus,
    DeliveryNoteStatus,
    MatchDecision,
    MatchStatus,
    ExceptionType,
    ExceptionStatus,
)

__all__ = [
    # Base
    "Base",
    # Invoices
    "Invoice",
    "InvoiceLine",
    "InvoiceStatus",
    # Purchase Orders
    "PurchaseOrder",
    "PurchaseOrderLine",
    "PurchaseOrderStatus",
    # Delivery Notes
    "DeliveryNote",
    "DeliveryNoteLine",
    "DeliveryNoteStatus",
    # Balance Ledger
    "BalanceLedger",
    # Cross Reference
    "CrossRef",
    # Enums
    "MatchDecision",
    "MatchStatus",
    "ExceptionType",
    "ExceptionStatus",
]
