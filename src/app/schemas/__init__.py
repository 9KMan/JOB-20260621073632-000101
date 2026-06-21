// src/app/schemas/__init__.py
"""Pydantic schemas for FinaRo AP Automation Core Engine."""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenData,
)
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    PurchaseOrderLineResponse,
)
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
)
from app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineUpdate,
    DeliveryNoteLineResponse,
)
from app.schemas.match import (
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchLineCreate,
    MatchLineUpdate,
    MatchLineResponse,
    MatchDecisionUpdate,
)
from app.schemas.balance import (
    BalanceCreate,
    BalanceUpdate,
    BalanceResponse,
    BalanceTransactionCreate,
    BalanceTransactionResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    # Supplier
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineUpdate",
    "PurchaseOrderLineResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceLineCreate",
    "InvoiceLineUpdate",
    "InvoiceLineResponse",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineUpdate",
    "DeliveryNoteLineResponse",
    # Match
    "MatchCreate",
    "MatchUpdate",
    "MatchResponse",
    "MatchLineCreate",
    "MatchLineUpdate",
    "MatchLineResponse",
    "MatchDecisionUpdate",
    # Balance
    "BalanceCreate",
    "BalanceUpdate",
    "BalanceResponse",
    "BalanceTransactionCreate",
    "BalanceTransactionResponse",
]
