# api/v1/delivery_notes.py
"""Delivery note endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    PaginatedResponse,
    SuccessResponse,
)
from core.database import get_db
from models import DeliveryNote, DeliveryNoteLine

router = APIRouter()


@router.post(
    "/",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a delivery note",
)
async def ingest_delivery_note(
    payload: DeliveryNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNoteResponse:
    """Ingest a delivery note (goods receipt) from ERP/OCR."""
    existing = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == payload.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note {payload.dn_number} already exists",
        )

    # Look up linked PO by number if provided
    po_id = None
    if payload.po_number:
        po_result = await db.execute(
            select(PurchaseOrder.id).where(PurchaseOrder.po_number == payload.po_number)
        )
        po_id = po_result.scalar_one_or_none()

    dn = DeliveryNote(
        dn_number=payload.dn_number,
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        po_id=po_id,
        po_number=payload.po_number,
        currency=payload.currency,
        dn_date=payload.dn_date,
        received_date=payload.received_date,
        notes=payload.notes,
    )

    for line_payload in payload.lines:
        line = DeliveryNoteLine(
            line_number=line_payload.line_number,
            description=line_payload.description,
            quantity_delivered=line_payload.quantity_delivered,
        )
        dn.lines.append(line)

    db.add(dn)
    await db.flush()
    await db.refresh(dn)
    return DeliveryNoteResponse.model_validate(dn)


@router.get(
    "/",
    response_model=PaginatedResponse[DeliveryNoteResponse],
    summary="List delivery notes",
)
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor_code: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[DeliveryNoteResponse]:
    """List delivery notes with optional filtering."""
    query = select(DeliveryNote).where(DeliveryNote.is_active == True)  # noqa: E712

    if vendor_code:
        query = query.where(DeliveryNote.vendor_code == vendor_code)
    if status_filter:
        query = query.where(DeliveryNote.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    dns = result.scalars().all()

    items = [DeliveryNoteResponse.model_validate(dn) for dn in dns]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponse,
    summary="Get a delivery note",
)
async def get_delivery_note(
    dn_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNoteResponse:
    """Retrieve a delivery note by ID."""
    result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    dn = result.scalar_one_or_none()
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note {dn_id} not found",
        )
    return DeliveryNoteResponse.model_validate(dn)
