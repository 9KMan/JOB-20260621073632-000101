// src/api/schemas/__init__.py
"""Pydantic schemas for API request/response validation."""
from src.api.schemas.common import (
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
)
from src.api.schemas.document import (
    DocumentCreate,
    DocumentLineCreate,
    DocumentLineResponse,
    DocumentResponse,
    DocumentUpdate,
)
from src.api.schemas.matching import (
    MatchResultResponse,
    MatchingRecordResponse,
    MatchScoreResponse,
)
from src.api.schemas.auth import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

__all__ = [
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationParams",
    "DocumentCreate",
    "DocumentLineCreate",
    "DocumentLineResponse",
    "DocumentResponse",
    "DocumentUpdate",
    "MatchResultResponse",
    "MatchingRecordResponse",
    "MatchScoreResponse",
    "TokenResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
]
