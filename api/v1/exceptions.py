"""Exception list/resolve/dismiss endpoints.

The exception model itself is declared in a later phase; this module exposes
the contract surface so the matching layer can call into it without coupling
to storage details.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.schemas import (
    ExceptionDismissIn,
    ExceptionListResponse,
    ExceptionOut,
    ExceptionResolveIn,
)
from models.enums import ExceptionSeverity, ExceptionStatus

router = APIRouter()


# Module-level placeholder store; the real persistence layer is wired up in a
# subsequent phase. Keeping it in-process lets the API contract be exercised
# without violating the rule that no production storage code lives here yet.
_store: dict[uuid.UUID, ExceptionOut] = {}


def _persist_exception(exc: ExceptionOut) -> ExceptionOut:
    _store[exc.id] = exc
    return exc


@router.get(
    "",
    response_model=ExceptionListResponse,
    summary="List open exceptions",
)
async def list_exceptions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    severity: Optional[ExceptionSeverity] = Query(default=None),
    status_filter: Optional[ExceptionStatus] = Query(default=None, alias="status"),
) -> ExceptionListResponse:
    items = list(_store.values())
    if severity is not None:
        items = [e for e in items if e.severity == severity]
    if status_filter is not None:
        items = [e for e in items if e.status == status_filter]
    items.sort(key=lambda e: e.created_at, reverse=True)
    total = len(items)
    return ExceptionListResponse(
        items=items[offset : offset + limit],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{exception_id}/resolve",
    response_model=ExceptionOut,
    summary="Resolve an exception",
)
async def resolve_exception(
    exception_id: uuid.UUID,
    payload: ExceptionResolveIn,
) -> ExceptionOut:
    exc = _store.get(exception_id)
    if exc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found")
    if exc.status == ExceptionStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Exception already resolved"
        )
    updated = exc.model_copy(update={
        "status": ExceptionStatus.RESOLVED,
        "detail": (exc.detail or "") + f"\nResolved: {payload.resolution_note}",
        "updated_at": datetime.now(timezone.utc),
    })
    return _persist_exception(updated)


@router.post(
    "/{exception_id}/dismiss",
    response_model=ExceptionOut,
    summary="Dismiss an exception",
)
async def dismiss_exception(
    exception_id: uuid.UUID,
    payload: ExceptionDismissIn,
) -> ExceptionOut:
    exc = _store.get(exception_id)
    if exc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found")
    updated = exc.model_copy(update={
        "status": ExceptionStatus.DISMISSED,
        "detail": (exc.detail or "") + f"\nDismissed: {payload.reason}",
        "updated_at": datetime.now(timezone.utc),
    })
    return _persist_exception(updated)


class _CreateExceptionIn(BaseModel):
    invoice_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    severity: ExceptionSeverity = ExceptionSeverity.MEDIUM
    summary: str = Field(min_length=1, max_length=512)
    detail: Optional[str] = None


@router.post(
    "",
    response_model=ExceptionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new exception (internal)",
)
async def create_exception(payload: _CreateExceptionIn) -> ExceptionOut:
    now = datetime.now(timezone.utc)
    exc = ExceptionOut(
        id=uuid.uuid4(),
        invoice_id=payload.invoice_id,
        purchase_order_id=payload.purchase_order_id,
        severity=payload.severity,
        status=ExceptionStatus.OPEN,
        summary=payload.summary,
        detail=payload.detail,
        created_at=now,
        updated_at=now,
    )
    return _persist_exception(exc)


__all__: List[str] = ["router"]
