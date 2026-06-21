# api/v1/delivery_notes.py
"""Delivery note endpoints."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreateSchema,
    DeliveryNoteResponseSchema,
    ErrorResponse,
)
from core.database import get_db
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

router = APIRouter()


@router.post(
    "/",
    response_model=DeliveryNoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_delivery_note(
    dn_data: DeliveryNoteCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNote:
    """
    Ingest a new delivery note from ERP/OCR.
    
    Creates the DN header and line items.
    Optionally links to a purchase order.
    """
    # Check for duplicate DN number
    existing = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note with number '{dn_data.dn_number}' already exists",
        )

    # Create delivery note
    delivery_note = DeliveryNote(
        vendor_id=dn_data.vendor_id,
        vendor_name=dn_data.vendor_name,
        dn_number=dn_data.dn_number,
        dn_date=dn_data.dn_date,
        receipt_date=dn_data.receipt_date,
        purchase_order_id=dn_data.purchase_order_id,
        status=DeliveryNoteStatus.RECEIVED.value,
        notes=dn_data.notes,
    )
    db.add(delivery_note)
    await db.flush()

    # Create DN lines
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            delivery_note_id=delivery_note.id,
            line_number=line_data.line_number,
            description=line_data.description,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            po_line_id=line_data.po_line_id,
        )
        db.add(line)

    await db.commit()
    await db.refresh(delivery_note)

    return delivery_note


@router.get(
    "/",
    response_model=list[DeliveryNoteResponseSchema],
)
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    from_date: Annotated[date | None, Query(alias="fromDate")] = None,
    to_date: Annotated[date | None, Query(alias="toDate")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[DeliveryNote]:
    """List delivery notes with optional filtering and pagination."""
    query = select(DeliveryNote).where(DeliveryNote.is_deleted == False)

    if vendor_id:
        query = query.where(DeliveryNote.vendor_id == vendor_id)
    if status:
        query = query.where(DeliveryNote.status == status)
    if from_date:
        query = query.where(DeliveryNote.dn_date >= from_date)
    if to_date:
        query = query.where(DeliveryNote.dn_date <= to_date)

    query = query.offset((page - 1) * per_page).limit(per_page)
    query = query.order_by(DeliveryNote.dn_date.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponseSchema,
    responses={404: {"model": ErrorResponse}},
)
async def get_delivery_note(
    dn_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNote:
    """Get delivery note by ID with all line items."""
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.id == dn_id)
    )
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note with ID '{dn_id}' not found",
        )

    return delivery_note


@router.get(
    "/number/{dn_number}",
    response_model=DeliveryNoteResponseSchema,
    responses={404: {"model": ErrorResponse}},
)
async def get_delivery_note_by_number(
    dn_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNote:
    """Get delivery note by DN number with all line items."""
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_number)
    )
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note with number '{dn_number}' not found",
        )

    return delivery_note
