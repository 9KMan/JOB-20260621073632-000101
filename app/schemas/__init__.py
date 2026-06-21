# app/schemas/__init__.py
"""Pydantic schemas for API request/response validation."""
from app.schemas.auth import (
    Token,
    TokenData,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
)
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorListResponse,
)
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineResponse,
    PurchaseOrderListResponse,
)
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceLineCreate,
    InvoiceLineResponse,
    InvoiceListResponse,
)
from app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineResponse,
    DeliveryNoteListResponse,
)
from app.schemas.matching import (
    MatchingRequest,
    MatchingResponse,
    MatchLineResultResponse,
    MatchConfirmationRequest,
    MatchingResultListResponse,
)
from app.schemas.balance import (
    BalanceResponse,
    BalanceListResponse,
    BalanceReconciliationRequest,
)

__all__ = [
    # Auth
    "Token",
    "TokenData",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    # Vendor
    "VendorCreate",
    "VendorUpdate",
    "VendorResponse",
    "VendorListResponse",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineResponse",
    "PurchaseOrderListResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceLineCreate",
    "InvoiceLineResponse",
    "InvoiceListResponse",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineResponse",
    "DeliveryNoteListResponse",
    # Matching
    "MatchingRequest",
    "MatchingResponse",
    "MatchLineResultResponse",
    "MatchConfirmationRequest",
    "MatchingResultListResponse",
    # Balance
    "BalanceResponse",
    "BalanceListResponse",
    "BalanceReconciliationRequest",
]
