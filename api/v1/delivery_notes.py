"""Delivery note ingestion and lookup endpoints."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import DeliveryNoteIn, DeliveryNoteListResponse, DeliveryNoteOut
from core.database import get_session
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.enums import DocumentStatus

router = APIRouter()


@router.post(
    "",
    response_model=DeliveryNoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a delivery note (ERP or OCR)",
)
async def create_delivery_note(
    payload: DeliveryNoteIn,
    session: AsyncSession = Depends(get_session),
) -> DeliveryNoteOut:
    note = DeliveryNote(
        dn_number=payload.dn_number,
        vendor_id=payload.vendor_id,
        purchase_order_id=payload.purchase_order_id,
        delivery_date=payload.delivery_date,
        received_by=payload.received_by,
        warehouse=payload.warehouse,
        is_ocr=payload.is_ocr,
        raw_payload=payload.raw_payload,
        status=DocumentStatus.INGESTED,
    )
    for line in payload.lines:
        note.lines.append(_line_from_payload(line))  # type: ignore[arg-type]
    session.add(note)
    await session.flush()
    await session.refresh(note, attribute_names=["lines"])
    return DeliveryNoteOut.model_validate(note)


@router.get(
    "",
    response_model=DeliveryNoteListResponse,
    summary="List delivery notes",
)
async def list_delivery_notes(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    vendor_id: Optional[uuid.UUID] = Query(default=None),
    purchase_order_id: Optional[uuid.UUID] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> DeliveryNoteListResponse:
    stmt = select(DeliveryNote).order_by(DeliveryNote.created_at.desc())
    count_stmt = select(func.count()).select_from(DeliveryNote)
    if vendor_id is not None:
        stmt = stmt.where(DeliveryNote.vendor_id == vendor_id)
        count_stmt = count_stmt.where(DeliveryNote.vendor_id == vendor_id)
    if purchase_order_id is not None:
        stmt = stmt.where(DeliveryNote.purchase_order_id == purchase_order_id)
        count_stmt = count_stmt.where(DeliveryNote.purchase_order_id == purchase_order_id)

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    items = [DeliveryNoteOut.model_validate(row) for row in result.scalars().all()]
    return DeliveryNoteListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteOut,
    summary="Get delivery note by id",
)
async def get_delivery_note(
    dn_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> DeliveryNoteOut:
    note = await session.get(DeliveryNote, dn_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery note not found")
    return DeliveryNoteOut.model_validate(note)


def _line_from_payload(line):  # type: ignore[no-untyped-def]
    return DeliveryNoteLine(
        line_number=line.line_number,
        sku=line.sku,
        description=line.description,
        received_qty=line.received_qty,
        uom=line.uom,
        purchase_order_line_id=line.purchase_order_line_id,
    )
