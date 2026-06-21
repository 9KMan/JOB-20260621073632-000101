// api/schemas/__init__.py
"""Pydantic schemas for API request/response validation."""

from api.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    MessageResponse,
    ErrorResponse,
)
from api.schemas.auth import (
    Token,
    TokenData,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
)
from api.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    PurchaseOrderLineResponse,
)
from api.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
)
from api.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteListResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineUpdate,
    DeliveryNoteLineResponse,
)
from api.schemas.match import (
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchListResponse,
    MatchLineResponse,
    MatchDecisionRequest,
    MatchScoreBreakdown,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "MessageResponse",
    "ErrorResponse",
    # Auth
    "Token",
    "TokenData",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    # Purchase Orders
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderListResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineUpdate",
    "PurchaseOrderLineResponse",
    # Invoices
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "InvoiceLineCreate",
    "InvoiceLineUpdate",
    "InvoiceLineResponse",
    # Delivery Notes
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteListResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineUpdate",
    "DeliveryNoteLineResponse",
    # Matches
    "MatchCreate",
    "MatchUpdate",
    "MatchResponse",
    "MatchListResponse",
    "MatchLineResponse",
    "MatchDecisionRequest",
    "MatchScoreBreakdown",
]
