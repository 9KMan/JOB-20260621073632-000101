// src/schemas/__init__.py
"""Pydantic schemas for API validation."""
from src.schemas.common import PaginatedResponse, ErrorResponse
from src.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse,
)
from src.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineResponse,
)
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceLineCreate,
    InvoiceLineResponse,
)
from src.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteListResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineResponse,
)
from src.schemas.matching import (
    MatchRequest,
    MatchResponse,
    MatchRecordResponse,
    MatchRecordListResponse,
    BalanceLedgerResponse,
    CrossReferenceCreate,
    CrossReferenceResponse,
    MatchDecisionRequest,
)
from src.schemas.auth import (
    Token,
    TokenData,
    UserCreate,
    UserResponse,
    LoginRequest,
)

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    "SupplierListResponse",
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderListResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineResponse",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "InvoiceLineCreate",
    "InvoiceLineResponse",
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteListResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineResponse",
    "MatchRequest",
    "MatchResponse",
    "MatchRecordResponse",
    "MatchRecordListResponse",
    "BalanceLedgerResponse",
    "CrossReferenceCreate",
    "CrossReferenceResponse",
    "MatchDecisionRequest",
    "Token",
    "TokenData",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
]
