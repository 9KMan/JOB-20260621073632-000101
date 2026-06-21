// api/schemas/__init__.py
"""Pydantic schemas for API request/response validation."""

from api.schemas.auth import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload,
)
from api.schemas.documents import (
    POLineCreate,
    POLineResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    InvoiceLineCreate,
    InvoiceLineResponse,
    InvoiceCreate,
    InvoiceResponse,
    DeliveryNoteLineCreate,
    DeliveryNoteLineResponse,
    DeliveryNoteCreate,
    DeliveryNoteResponse,
)
from api.schemas.matching import (
    MatchResponse,
    MatchCreate,
    MatchResult,
    MatchingResult,
    MatchLineDetailResponse,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    # Documents
    "POLineCreate",
    "POLineResponse",
    "PurchaseOrderCreate",
    "PurchaseOrderResponse",
    "InvoiceLineCreate",
    "InvoiceLineResponse",
    "InvoiceCreate",
    "InvoiceResponse",
    "DeliveryNoteLineCreate",
    "DeliveryNoteLineResponse",
    "DeliveryNoteCreate",
    "DeliveryNoteResponse",
    # Matching
    "MatchResponse",
    "MatchCreate",
    "MatchResult",
    "MatchingResult",
    "MatchLineDetailResponse",
]
