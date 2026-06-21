// models/__init__.py
"""Database models for AP Automation Core Engine.

This module exports all SQLAlchemy models used in the application.
Models are organized by domain: invoices, purchase orders, delivery notes,
balance ledger, and cross-reference (learning loop).

All models use UUID primary keys and include created_at/updated_at timestamps
as specified in the project requirements.
"""

from models.base import Base
from models.enums import (
    InvoiceStatus,
    PurchaseOrderStatus,
    DeliveryNoteStatus,
    MatchStatus,
    MatchDecision,
    ExceptionType,
    ExceptionStatus,
    LineStatus,
)
from models.invoice import Invoice, InvoiceLine
from models.purchase_order import PurchaseOrder, POLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.balance_ledger import BalanceLedger
from models.cross_ref import CrossRef

__all__ = [
    # Base
    "Base",
    # Enums
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchStatus",
    "MatchDecision",
    "ExceptionType",
    "ExceptionStatus",
    "LineStatus",
    # Models
    "Invoice",
    "InvoiceLine",
    "PurchaseOrder",
    "POLine",
    "DeliveryNote",
    "DeliveryNoteLine",
    "BalanceLedger",
    "CrossRef",
]

# Model registry for migrations and utilities
MODEL_REGISTRY = {
    "invoice": Invoice,
    "invoice_line": InvoiceLine,
    "purchase_order": PurchaseOrder,
    "po_line": POLine,
    "delivery_note": DeliveryNote,
    "delivery_note_line": DeliveryNoteLine,
    "balance_ledger": BalanceLedger,
    "cross_ref": CrossRef,
}


def get_all_models():
    """Get all model classes for registration."""
    return [
        Invoice,
        InvoiceLine,
        PurchaseOrder,
        POLine,
        DeliveryNote,
        DeliveryNoteLine,
        BalanceLedger,
        CrossRef,
    ]
