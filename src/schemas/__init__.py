// src/schemas/__init__.py
"""Pydantic schemas package for request/response validation."""
from app.schemas.base import BaseSchema, BaseResponse, PaginatedResponse
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    PurchaseOrderLineResponse,
)
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
)
from app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteListResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineUpdate,
    DeliveryNoteLineResponse,
)
from app.schemas.match import (
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchListResponse,
    MatchDecisionRequest,
    MatchResultResponse,
)
from app.schemas.balance import (
    BalanceLedgerCreate,
    BalanceLedgerUpdate,
    BalanceLedgerResponse,
    BalanceLedgerListResponse,
)

__all__ = [
    "BaseSchema",
    "BaseResponse",
    "PaginatedResponse",
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
    # Match
    "MatchCreate",
    "MatchUpdate",
    "MatchResponse",
    "MatchListResponse",
    "MatchDecisionRequest",
    "MatchResultResponse",
    # Balance
    "BalanceLedgerCreate",
    "BalanceLedgerUpdate",
    "BalanceLedgerResponse",
    "BalanceLedgerListResponse",
]
