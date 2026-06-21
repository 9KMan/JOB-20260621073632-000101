// src/schemas/__init__.py
"""Pydantic schemas for request/response validation."""
from src.schemas.base import BaseSchema, PaginatedResponse
from src.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin
)
from src.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse
)
from src.schemas.purchase_order import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    PurchaseOrderLineCreate, PurchaseOrderLineResponse
)
from src.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceLineCreate, InvoiceLineResponse
)
from src.schemas.delivery_note import (
    DeliveryNoteCreate, DeliveryNoteUpdate, DeliveryNoteResponse,
    DeliveryNoteLineCreate, DeliveryNoteLineResponse
)
from src.schemas.matching import (
    MatchCreate, MatchUpdate, MatchResponse, MatchScoreResponse,
    BalanceEntryResponse, MatchReview
)
from src.schemas.auth import Token, TokenPayload

__all__ = [
    "BaseSchema",
    "PaginatedResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineResponse",
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceLineCreate",
    "InvoiceLineResponse",
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineResponse",
    "MatchCreate",
    "MatchUpdate",
    "MatchResponse",
    "MatchScoreResponse",
    "BalanceEntryResponse",
    "MatchReview",
    "Token",
    "TokenPayload",
]
