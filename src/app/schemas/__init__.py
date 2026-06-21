// src/app/schemas/__init__.py
"""Pydantic schemas initialization."""
from app.schemas.auth import (
    TokenSchema,
    TokenPayload,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
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
    PurchaseOrderLineResponse,
)
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceLineCreate,
    InvoiceLineResponse,
)
from app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineResponse,
)
from app.schemas.match import (
    MatchResultCreate,
    MatchResultResponse,
    MatchResultUpdate,
    MatchConfirmationRequest,
    MatchSearchParams,
)
from app.schemas.balance import (
    BalanceLedgerCreate,
    BalanceLedgerResponse,
    BalanceLedgerUpdate,
)
from app.schemas.common import (
    PaginatedResponse,
    SearchParams,
    MessageResponse,
    ErrorResponse,
)

__all__ = [
    # Auth
    "TokenSchema",
    "TokenPayload",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    # Supplier
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceLineCreate",
    "InvoiceLineResponse",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineResponse",
    # Match
    "MatchResultCreate",
    "MatchResultResponse",
    "MatchResultUpdate",
    "MatchConfirmationRequest",
    "MatchSearchParams",
    # Balance
    "BalanceLedgerCreate",
    "BalanceLedgerResponse",
    "BalanceLedgerUpdate",
    # Common
    "PaginatedResponse",
    "SearchParams",
    "MessageResponse",
    "ErrorResponse",
]
