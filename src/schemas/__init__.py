// src/schemas/__init__.py
"""Pydantic schemas package."""
from src.schemas.auth import (
    Token,
    TokenData,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
)
from src.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from src.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    PurchaseOrderLineResponse,
)
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
)
from src.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineUpdate,
    DeliveryNoteLineResponse,
)
from src.schemas.match import (
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchLineCreate,
    MatchLineUpdate,
    MatchLineResponse,
    BalanceLedgerResponse,
    MatchResultResponse,
    ConfirmMatchRequest,
    RejectMatchRequest,
)
from src.schemas.common import (
    PaginatedResponse,
    MessageResponse,
    ErrorResponse,
)

__all__ = [
    # Auth
    "Token",
    "TokenData",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
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
    "BalanceLedgerResponse",
    "MatchResultResponse",
    "ConfirmMatchRequest",
    "RejectMatchRequest",
    # Common
    "PaginatedResponse",
    "MessageResponse",
    "ErrorResponse",
]
