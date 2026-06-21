// src/app/schemas/__init__.py
"""API schemas."""
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    Token,
    TokenPayload,
    UserCreate,
    UserInDB,
    UserResponse,
    UserUpdate,
)
from app.schemas.balance import (
    BalanceLedgerCreate,
    BalanceLedgerDetailResponse,
    BalanceLedgerListResponse,
    BalanceLedgerResponse,
    BalanceLedgerUpdate,
    PurchaseOrderBalanceSummary,
    SupplierBalanceSummary,
)
from app.schemas.base import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    UUIDSchema,
)
from app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteDetailResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineResponse,
    DeliveryNoteLineUpdate,
    DeliveryNoteListResponse,
    DeliveryNoteResponse,
    DeliveryNoteUpdate,
)
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceDetailResponse,
    InvoiceLineCreate,
    InvoiceLineResponse,
    InvoiceLineUpdate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)
from app.schemas.match import (
    MatchConfirmationCreate,
    MatchConfirmationResponse,
    MatchCreate,
    MatchDetailResponse,
    MatchLineDetailResponse,
    MatchListResponse,
    MatchResponse,
    MatchScoreSummary,
    MatchUpdate,
)
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineResponse,
    PurchaseOrderLineUpdate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from app.schemas.supplier import (
    SupplierCreate,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "RefreshTokenRequest",
    "Token",
    "TokenPayload",
    "UserCreate",
    "UserInDB",
    "UserResponse",
    "UserUpdate",
    # Balance
    "BalanceLedgerCreate",
    "BalanceLedgerDetailResponse",
    "BalanceLedgerListResponse",
    "BalanceLedgerResponse",
    "BalanceLedgerUpdate",
    "PurchaseOrderBalanceSummary",
    "SupplierBalanceSummary",
    # Base
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
    "SuccessResponse",
    "UUIDSchema",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteDetailResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineResponse",
    "DeliveryNoteLineUpdate",
    "DeliveryNoteListResponse",
    "DeliveryNoteResponse",
    "DeliveryNoteUpdate",
    # Invoice
    "InvoiceCreate",
    "InvoiceDetailResponse",
    "InvoiceLineCreate",
    "InvoiceLineResponse",
    "InvoiceLineUpdate",
    "InvoiceListResponse",
    "InvoiceResponse",
    "InvoiceUpdate",
    # Match
    "MatchConfirmationCreate",
    "MatchConfirmationResponse",
    "MatchCreate",
    "MatchDetailResponse",
    "MatchLineDetailResponse",
    "MatchListResponse",
    "MatchResponse",
    "MatchScoreSummary",
    "MatchUpdate",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderDetailResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineResponse",
    "PurchaseOrderLineUpdate",
    "PurchaseOrderListResponse",
    "PurchaseOrderResponse",
    "PurchaseOrderUpdate",
    # Supplier
    "SupplierCreate",
    "SupplierListResponse",
    "SupplierResponse",
    "SupplierUpdate",
]
