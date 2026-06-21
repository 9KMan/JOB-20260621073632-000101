// api/v1/delivery_notes.py
"""Delivery note ingestion and retrieval endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    APIErrorResponse,
    APIListResponse,
    DeliveryNoteCreate,
    DeliveryNoteListItem,
    DeliveryNoteResponse,
    PaginationParams,
)
from core.database import get_db_session
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": APIErrorResponse}},
)
async def ingest_delivery_note(
    payload: DeliveryNoteCreate,
    session: AsyncSession = Depends(get_db_session),
) -> DeliveryNoteResponse:
    """
    Ingest a delivery note (goods receipt) from ERP or OCR processing.

    The DN number must be unique.
    """
    existing = await session.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == payload.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DN number '{payload.dn_number}' already exists.",
        )

    dn = DeliveryNote(
        dn_number=payload.dn_number,
        vendor_number=payload.vendor_number,
        vendor_name=payload.vendor_name,
        po_reference_id=payload.po_reference_id,
        dn_date=payload.dn_date,
        received_date=payload.received_date,
        total_amount=payload.total_amount,
        currency=payload.currency,
        notes=payload.notes,
        external_reference=payload.external_reference,
        status=DeliveryNoteStatus.CONFIRMED,
    )
    session.add(dn)
    await session.flush()

    for line_payload in payload.lines:
        line = DeliveryNoteLine(
            dn_id=dn.id,
            line_number=line_payload.line_number,
            description=line_payload.description,
            sku=line_payload.sku,
            quantity=line_payload.quantity,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
            po_line_id=line_payload.po_line_id,
        )
        session.add(line)

    await session.commit()
    await session.refresh(dn)
    logger.info("DN ingested: id=%s number=%s", dn.id, dn.dn_number)
    return DeliveryNoteResponse.model_validate(dn)


@router.get("", response_model=APIListResponse[DeliveryNoteListItem])
async def list_delivery_notes(
    session: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(),
    status_filter: DeliveryNoteStatus | None = Query(None, alias="status"),
    vendor_number: str | None = Query(None, max_length=50),
) -> APIListResponse[DeliveryNoteListItem]:
    """Paginated list of delivery notes."""
    stmt = select(DeliveryNote).where(DeliveryNote.deleted_at.is_(None))

    if status_filter:
        stmt = stmt.where(DeliveryNote.status == status_filter)
    if vendor_number:
        stmt = stmt.where(DeliveryNote.vendor_number == vendor_number)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(DeliveryNote.created_at.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await session.execute(stmt)
    dns = result.scalars().all()

    items = [DeliveryNoteListItem.model_validate(dn) for dn in dns]
    pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return APIListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(
    dn_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DeliveryNoteResponse:
    """Retrieve a single delivery note with its line items."""
    result = await session.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    dn = result.scalar_one_or_none()
    if not dn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery note not found")
    return DeliveryNoteResponse.model_validate(dn)
