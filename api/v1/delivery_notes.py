# api/v1/delivery_notes.py
"""Delivery note endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    PaginatedResponse,
    ErrorResponse,
)
from core.database import get_db
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

router = APIRouter()


@router.post(
    "/",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNoteResponse:
    """Create a new delivery note with line items."""
    existing = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note with number {dn_data.dn_number} already exists",
        )

    delivery_note = DeliveryNote(
        id=str(uuid4()),
        vendor_number=dn_data.vendor_number,
        vendor_name=dn_data.vendor_name,
        dn_number=dn_data.dn_number,
        dn_date=dn_data.dn_date,
        delivery_date=dn_data.delivery_date,
        po_reference=dn_data.po_reference,
        notes=dn_data.notes,
        status=DeliveryNoteStatus.CONFIRMED.value,
    )

    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            id=str(uuid4()),
            delivery_note_id=delivery_note.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            notes=line_data.notes,
            po_line_reference=line_data.po_line_reference,
        )
        delivery_note.lines.append(line)

    db.add(delivery_note)
    await db.flush()
    await db.refresh(delivery_note)

    return DeliveryNoteResponse.model_validate(delivery_note)


@router.get(
    "/",
    response_model=PaginatedResponse[DeliveryNoteResponse],
)
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status: str | None = Query(None, description="Filter by status"),
    po_reference: str | None = Query(None, description="Filter by PO reference"),
) -> PaginatedResponse[DeliveryNoteResponse]:
    """List all delivery notes with pagination and filtering."""
    query = select(DeliveryNote).where(DeliveryNote.is_active == True)

    if vendor_number:
        query = query.where(DeliveryNote.vendor_number == vendor_number)
    if status:
        query = query.where(DeliveryNote.status == status)
    if po_reference:
        query = query.where(DeliveryNote.po_reference == po_reference)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(DeliveryNote.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    delivery_notes = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=[DeliveryNoteResponse.model_validate(dn) for dn in delivery_notes],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_delivery_note(
    dn_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNoteResponse:
    """Get a specific delivery note by ID."""
    result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note with ID {dn_id} not found",
        )

    return DeliveryNoteResponse.model_validate(delivery_note)
