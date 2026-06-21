# models/__init__.py
"""Models package - SQLAlchemy ORM models."""

from models.base import Base
from models.balance_ledger import BalanceLedger
from models.cross_ref import CrossRef
from models.delivery_note import DeliveryNote
from models.enums import (
    DecisionStatus,
    DocumentStatus,
    ExceptionReason,
    InvoiceStatus,
    LineStatus,
    MatchDecision,
    MatchScoreLevel,
    PurchaseOrderStatus,
)
from models.invoice import Invoice
from models.purchase_order import PurchaseOrder

__all__ = [
    # Base
    "Base",
    # Enums
    "DocumentStatus",
    "InvoiceStatus",
    "PurchaseOrderStatus",
    "LineStatus",
    "MatchDecision",
    "MatchScoreLevel",
    "DecisionStatus",
    "ExceptionReason",
    # Models
    "Invoice",
    "PurchaseOrder",
    "DeliveryNote",
    "BalanceLedger",
    "CrossRef",
]


def register_models() -> None:
    """Import all models to ensure they are registered with Base."""
    from models import (
        balance_ledger,
        cross_ref,
        delivery_note,
        invoice,
        purchase_order,
    )
    # Models are imported to trigger SQLAlchemy model registration
    _ = (
        balance_ledger,
        cross_ref,
        delivery_note,
        invoice,
        purchase_order,
    )
