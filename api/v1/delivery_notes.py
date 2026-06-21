# api/v1/delivery_notes.py
"""Delivery Note endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models import DeliveryNote, DeliveryNoteLine
from api.schemas import (
    BaseResponse,
    PaginatedResponse,
    DeliveryNoteCreate,
    DeliveryNoteResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=BaseResponse[DeliveryNoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new delivery note",
    description="Create a new delivery note from ERP or OCR source.",
)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[DeliveryNoteResponse]:
    """Ingest a new delivery note."""
    # Check for duplicate DN number
    existing = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note {dn_data.dn_number} already exists",
        )
    
    # Create DN
    delivery_note = DeliveryNote(
        dn_number=dn_data.dn_number,
        vendor_id=dn_data.vendor_id,
        vendor_name=dn_data.vendor_name,
        po_number=dn_data.po_number,
        delivery_date=dn_data.delivery_date,
        currency=dn_data.currency,
        total_amount=dn_data.total_amount,
        notes=dn_data.notes,
        source_system=dn_data.source_system,
        metadata_=dn_data.metadata,
        status="issued",
    )
    db.add(delivery_note)
    await db.flush()
    
    # Create line items
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            delivery_note_id=delivery_note.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            po_line_id=line_data.po_line_id,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(delivery_note)
    
    # Load lines relationship
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == delivery_note.id)
    )
    delivery_note = result.scalar_one()
    
    return BaseResponse(
        success=True,
        data=DeliveryNoteResponse.model_validate(delivery_note),
        message="Delivery note created successfully",
    )


@router.get(
    "/",
    response_model=PaginatedResponse[DeliveryNoteResponse],
    summary="List delivery notes",
    description="Get paginated list of delivery notes with optional filters.",
)
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    vendor_id: str | None = None,
    po_number: str | None = None,
    status: str | None = None,
    delivery_date_from: str | None = None,
    delivery_date_to: str | None = None,
) -> PaginatedResponse[DeliveryNoteResponse]:
    """List delivery notes with pagination and filters."""
    query = select(DeliveryNote).options(selectinload(DeliveryNote.lines))
    count_query = select(func.count(DeliveryNote.id))
    
    # Apply filters
    if vendor_id:
        query = query.where(DeliveryNote.vendor_id == vendor_id)
        count_query = count_query.where(DeliveryNote.vendor_id == vendor_id)
    if po_number:
        query = query.where(DeliveryNote.po_number == po_number)
        count_query = count_query.where(DeliveryNote.po_number == po_number)
    if status:
        query = query.where(DeliveryNote.status == status)
        count_query = count_query.where(DeliveryNote.status == status)
    
    # Get total count
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.order_by(DeliveryNote.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    delivery_notes = result.scalars().all()
    
    pages = (total + per_page - 1) // per_page if total else 1
    
    return PaginatedResponse(
        success=True,
        data=[DeliveryNoteResponse.model_validate(dn) for dn in delivery_notes],
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/{dn_id}",
    response_model=BaseResponse[DeliveryNoteResponse],
    summary="Get delivery note by ID",
)
async def get_delivery_note(
    dn_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[DeliveryNoteResponse]:
    """Get a single delivery note by ID."""
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn_id)
    )
    delivery_note = result.scalar_one_or_none()
    
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note {dn_id} not found",
        )
    
    return BaseResponse(
        success=True,
        data=DeliveryNoteResponse.model_validate(delivery_note),
    )
