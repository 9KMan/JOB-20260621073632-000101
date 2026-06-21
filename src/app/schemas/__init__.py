# src/app/schemas/__init__.py
"""Pydantic schemas for API request/response validation."""
from src.app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from src.app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
)
from src.app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    PurchaseOrderLineResponse,
)
from src.app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
)
from src.app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteListResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineUpdate,
    DeliveryNoteLineResponse,
)
from src.app.schemas.matching import (
    MatchRequest,
    MatchResponse,
    MatchResultResponse,
    MatchScoreResponse,
    MatchReviewRequest,
    MatchDecisionResponse,
)
from src.app.schemas.balance import (
    BalanceResponse,
    BalanceListResponse,
    BalanceUpdateRequest,
)
from src.app.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Supplier
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    "SupplierListResponse",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderListResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineUpdate",
    "PurchaseOrderLineResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "InvoiceLineCreate",
    "InvoiceLineUpdate",
    "InvoiceLineResponse",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteListResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineUpdate",
    "DeliveryNoteLineResponse",
    # Matching
    "MatchRequest",
    "MatchResponse",
    "MatchResultResponse",
    "MatchScoreResponse",
    "MatchReviewRequest",
    "MatchDecisionResponse",
    # Balance
    "BalanceResponse",
    "BalanceListResponse",
    "BalanceUpdateRequest",
    # Auth
    "Token",
    "TokenData",
    "LoginRequest",
]
