# src/schemas/__init__.py
"""Pydantic schemas package."""
from src.schemas.user import UserCreate, UserUpdate, UserInDB, UserResponse
from src.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderInDB,
    PurchaseOrderResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    PurchaseOrderLineInDB,
    PurchaseOrderLineResponse,
)
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceInDB,
    InvoiceResponse,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineInDB,
    InvoiceLineResponse,
)
from src.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteInDB,
    DeliveryNoteResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineUpdate,
    DeliveryNoteLineInDB,
    DeliveryNoteLineResponse,
)
from src.schemas.matching import (
    MatchingRecordCreate,
    MatchingRecordUpdate,
    MatchingRecordInDB,
    MatchingRecordResponse,
    MatchingLineCreate,
    MatchingLineUpdate,
    MatchingLineInDB,
    MatchingLineResponse,
)
from src.schemas.balance_ledger import (
    BalanceLedgerCreate,
    BalanceLedgerUpdate,
    BalanceLedgerInDB,
    BalanceLedgerResponse,
)
from src.schemas.common import Token, TokenData, Message, PaginationParams, PaginatedResponse

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    # Purchase Order
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderInDB",
    "PurchaseOrderResponse",
    "PurchaseOrderLineCreate",
    "PurchaseOrderLineUpdate",
    "PurchaseOrderLineInDB",
    "PurchaseOrderLineResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceInDB",
    "InvoiceResponse",
    "InvoiceLineCreate",
    "InvoiceLineUpdate",
    "InvoiceLineInDB",
    "InvoiceLineResponse",
    # Delivery Note
    "DeliveryNoteCreate",
    "DeliveryNoteUpdate",
    "DeliveryNoteInDB",
    "DeliveryNoteResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineUpdate",
    "DeliveryNoteLineInDB",
    "DeliveryNoteLineResponse",
    # Matching
    "MatchingRecordCreate",
    "MatchingRecordUpdate",
    "MatchingRecordInDB",
    "MatchingRecordResponse",
    "MatchingLineCreate",
    "MatchingLineUpdate",
    "MatchingLineInDB",
    "MatchingLineResponse",
    # Balance Ledger
    "BalanceLedgerCreate",
    "BalanceLedgerUpdate",
    "BalanceLedgerInDB",
    "BalanceLedgerResponse",
    # Common
    "Token",
    "TokenData",
    "Message",
    "PaginationParams",
    "PaginatedResponse",
]
