// api/v1/delivery_notes.py
"""Delivery Note API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.enums import DeliveryNoteStatus
from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    DeliveryNoteDetailResponse,
    PaginatedResponse,
    PaginationMeta,
)

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new delivery note",
)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: DB,
) -> DeliveryNote:
    """Ingest a new delivery note from ERP/OCR system.
    
    Creates a new delivery note with optional line items.
    """
    # Check for duplicate DN number
    existing = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note with number {dn_data.dn_number} already exists",
        )
    
    # Create delivery note
    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        po_id=dn_data.po_id,
        delivery_date=dn_data.delivery_date,
        received_date=dn_data.received_date,
        total_amount=dn_data.total_amount,
        currency=dn_data.currency,
        status=DeliveryNoteStatus.SUBMITTED,
        notes=dn_data.notes,
        erp_reference=dn_data.erp_reference,
    )
    db.add(dn)
    await db.flush()
    
    # Create line items
    for item_data in dn_data.line_items:
        line_item = DeliveryNoteLine(
            dn_id=dn.id,
            po_line_id=item_data.po_line_id,
            line_number=item_data.line_number,
            description=item_data.description,
            quantity=item_data.quantity,
            uom=item_data.uom,
            notes=item_data.notes,
        )
        db.add(line_item)
    
    await db.commit()
    await db.refresh(dn)
    
    return dn


@router.get(
    "",
    response_model=PaginatedResponse[DeliveryNoteResponse],
    summary="List all delivery notes",
)
async def list_delivery_notes(
    db: DB,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    supplier_id: str | None = Query(None, description="Filter by supplier"),
    po_id: UUID | None = Query(None, description="Filter by PO"),
    status: DeliveryNoteStatus | None = Query(None, description="Filter by status"),
    from_date: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
) -> PaginatedResponse[DeliveryNoteResponse]:
    """List all delivery notes with optional filters and pagination."""
    # Build base query
    query = select(DeliveryNote)
    count_query = select(func.count(DeliveryNote.id))
    
    # Apply filters
    if supplier_id:
        query = query.where(DeliveryNote.supplier_id == supplier_id)
        count_query = count_query.where(DeliveryNote.supplier_id == supplier_id)
    if po_id:
        query = query.where(DeliveryNote.po_id == po_id)
        count_query = count_query.where(DeliveryNote.po_id == po_id)
    if status:
        query = query.where(DeliveryNote.status == status)
        count_query = count_query.where(DeliveryNote.status == status)
    if from_date:
        query = query.where(DeliveryNote.delivery_date >= from_date)
        count_query = count_query.where(DeliveryNote.delivery_date >= from_date)
    if to_date:
        query = query.where(DeliveryNote.delivery_date <= to_date)
        count_query = count_query.where(DeliveryNote.delivery_date <= to_date)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(DeliveryNote.created_at.desc())
    
    result = await db.execute(query)
    dns = result.scalars().all()
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size
    meta = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    
    return PaginatedResponse(data=list(dns), meta=meta)


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteDetailResponse,
    summary="Get delivery note details",
)
async def get_delivery_note(
    dn_id: UUID,
    db: DB,
) -> DeliveryNote:
    """Get detailed delivery note information including line items."""
    query = (
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.line_items))
        .where(DeliveryNote.id == dn_id)
    )
    result = await db.execute(query)
    dn = result.scalar_one_or_none()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note with id {dn_id} not found",
        )
    
    return dn


@router.patch(
    "/{dn_id}/confirm",
    response_model=DeliveryNoteResponse,
    summary="Confirm delivery note",
)
async def confirm_delivery_note(
    dn_id: UUID,
    db: DB,
) -> DeliveryNote:
    """Confirm a delivery note as received."""
    result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    dn = result.scalar_one_or_none()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note with id {dn_id} not found",
        )
    
    dn.status = DeliveryNoteStatus.CONFIRMED
    await db.commit()
    await db.refresh(dn)
    
    return dn
