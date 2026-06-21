# models/__init__.py
"""Models package initialization.

Exports all SQLAlchemy models and enums for easy importing.
"""

from models.base import Base, UUIDMixin
from models.enums import (
    InvoiceStatus,
    PurchaseOrderStatus,
    DeliveryNoteStatus,
    MatchingStatus,
    DecisionType,
    ExceptionType,
    MatchConfidence,
    LearningStatus,
)
from models.invoice import Invoice, InvoiceLine
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.balance_ledger import BalanceLedger, BalanceType
from models.cross_ref import CrossRef, MatchSource


__all__ = [
    # Base
    "Base",
    "UUIDMixin",
    # Enums
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "DeliveryNoteStatus",
    "MatchingStatus",
    "DecisionType",
    "ExceptionType",
    "MatchConfidence",
    "LearningStatus",
    "BalanceType",
    "MatchSource",
    # Models
    "Invoice",
    "InvoiceLine",
    "PurchaseOrder",
    "PurchaseOrderLine",
    "DeliveryNote",
    "DeliveryNoteLine",
    "BalanceLedger",
    "CrossRef",
]


def import_all_models() -> None:
    """Import all models to ensure they are registered with SQLAlchemy."""
    from models import (
        invoice,
        purchase_order,
        delivery_note,
        balance_ledger,
        cross_ref,
    )
    # Models are imported for side-effect registration
    pass
