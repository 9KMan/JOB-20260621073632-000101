# api/v1/delivery_notes.py
"""Delivery note endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteListResponse,
    DeliveryNoteResponse,
    PaginatedResponse,
    PageParams,
)
from core.database import get_db
from core.security import get_current_user_id
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

router = APIRouter()


@router.post(
    "/",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new delivery note",
)
async def ingest_delivery_note(
    payload: DeliveryNoteCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> DeliveryNoteResponse:
    """Ingest a new delivery note with its line items."""
    existing = await db.execute(
        select(DeliveryNote.id).where(DeliveryNote.dn_number == payload.dn_number)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DN number '{payload.dn_number}' already exists",
        )

    dn = DeliveryNote(
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        dn_number=payload.dn_number,
        dn_date=payload.dn_date,
        receipt_date=payload.receipt_date,
        source=payload.source,
        status=DeliveryNoteStatus.RECEIVED,
        erp_dn_id=payload.erp_dn_id,
        po_id=payload.po_id,
    )
    db.add(dn)
    await db.flush()

    for line_payload in payload.lines:
        line = DeliveryNoteLine(
            dn_id=dn.id,
            line_number=line_payload.line_number,
            description=line_payload.description,
            product_code=line_payload.product_code,
            product_name=line_payload.product_name,
            quantity_delivered=line_payload.quantity_delivered,
            unit_of_measure=line_payload.unit_of_measure,
        )
        db.add(line)

    await db.commit()
    await db.refresh(dn)
    return DeliveryNoteResponse.model_validate(dn)


@router.get("/", response_model=PaginatedResponse)
async def list_delivery_notes(
    params: PageParams = Depends(),
    status_filter: DeliveryNoteStatus | None = Query(None, alias="status"),
    vendor_code: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> PaginatedResponse:
    """List all delivery notes with optional filtering and pagination."""
    stmt = select(DeliveryNote)
    count_stmt = select(func.count(DeliveryNote.id))

    if status_filter:
        stmt = stmt.where(DeliveryNote.status == status_filter)
        count_stmt = count_stmt.where(DeliveryNote.status == status_filter)
    if vendor_code:
        stmt = stmt.where(DeliveryNote.vendor_code == vendor_code)
        count_stmt = count_stmt.where(DeliveryNote.vendor_code == vendor_code)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(DeliveryNote.created_at.desc()).offset(params.offset).limit(params.page_size)
    rows = (await db.execute(stmt)).scalars().all()

    items = [DeliveryNoteListResponse.model_validate(r) for r in rows]
    return PaginatedResponse.create(items, total, params)


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(
    dn_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> DeliveryNoteResponse:
    """Retrieve a single delivery note with its line items."""
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.id == dn_id)
    )
    dn = result.scalar_one_or_none()
    if dn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note {dn_id} not found",
        )
    return DeliveryNoteResponse.model_validate(dn)
