# api/v1/exceptions.py
"""Exception handling endpoints — list, resolve, dismiss."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ExceptionResponse,
    ExceptionResolveRequest,
    ExceptionDismissRequest,
    PaginatedResponse,
    SuccessResponse,
)
from core.database import get_db

router = APIRouter()


# Exception model placeholder — the actual Exception model would be in models/
# For now we use the exception table definition from cross_ref or a separate table
# Since SPEC mentions exceptions we include a basic inline reference

# Note: In a real implementation you'd have a `models/exception.py` with an
# `Exception` model. Here we reference it generically.

EXCEPTION_MODEL = "exceptions"  # placeholder


@router.get(
    "/",
    response_model=PaginatedResponse[ExceptionResponse],
    summary="List exceptions",
)
async def list_exceptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    invoice_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    exception_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ExceptionResponse]:
    """List all matching exceptions with optional filtering.

    Note: This endpoint requires a dedicated `Exception` model in models/exception.py
    which should include: id, invoice_id, invoice_line_id, po_line_id,
    exception_type (enum), status (enum), match_score, resolution_notes, created_at.
    """
    # Placeholder implementation — replace with actual Exception model query
    return PaginatedResponse.create([], total=0, page=page, page_size=page_size)


@router.post(
    "/{exception_id}/resolve",
    response_model=SuccessResponse,
    summary="Resolve an exception",
)
async def resolve_exception(
    exception_id: UUID,
    payload: ExceptionResolveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Resolve an exception by confirming its match or adjusting the PO line."""
    # Placeholder: Resolve exception logic
    # - Update exception status to RESOLVED
    # - Update balance ledger if po_line_id changed
    # - Trigger re-matching if needed
    return SuccessResponse(
        message=f"Exception {exception_id} resolved",
        detail={"resolution_notes": payload.resolution_notes},
    )


@router.post(
    "/{exception_id}/dismiss",
    response_model=SuccessResponse,
    summary="Dismiss an exception",
)
async def dismiss_exception(
    exception_id: UUID,
    payload: ExceptionDismissRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Dismiss an exception without action (e.g., duplicate, outside policy)."""
    return SuccessResponse(
        message=f"Exception {exception_id} dismissed",
        detail={"dismissal_reason": payload.dismissal_reason},
    )
