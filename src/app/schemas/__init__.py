# src/app/schemas/__init__.py
"""Pydantic schemas for API request/response validation."""
from src.app.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserLogin,
    Token,
    TokenData,
)
from src.app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderRead,
    PurchaseOrderUpdate,
    PurchaseOrderLineCreate,
    PurchaseOrderLineRead,
)
from src.app.schemas.invoice import (
    InvoiceCreate,
    InvoiceRead,
    InvoiceUpdate,
    InvoiceLineCreate,
    InvoiceLineRead,
)
from src.app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteRead,
    DeliveryNoteUpdate,
    DeliveryNoteLineCreate,
    DeliveryNoteLineRead,
)
from src.app.schemas.matching import (
    MatchResultCreate,
    MatchResultRead,
    MatchResultUpdate,
    CrossReferenceCreate,
    CrossReferenceRead,
    MatchDecisionCreate,
    MatchDecisionRead,
)
from src.app.schemas.balances import (
    BalanceLedgerCreate,
    BalanceLedgerRead,
)
from src.app.schemas.common import (
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserLogin",
    "Token",
    "TokenData",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderRead",
    "PurchaseOrderUpdate",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineRead",
    # Invoice
    "InvoiceCreate",
    "InvoiceRead",
    "InvoiceUpdate",
    "InvoiceLineCreate",
    "InvoiceLineRead",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteRead",
    "DeliveryNoteUpdate",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineRead",
    # Matching
    "MatchResultCreate",
    "MatchResultRead",
    "MatchResultUpdate",
    "CrossReferenceCreate",
    "CrossReferenceRead",
    "MatchDecisionCreate",
    "MatchDecisionRead",
    # Balances
    "BalanceLedgerCreate",
    "BalanceLedgerRead",
    # Common
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]
