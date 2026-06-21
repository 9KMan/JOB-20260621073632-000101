# api/v1/delivery_notes.py
"""Delivery Note endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    PaginatedResponse,
    BaseResponse,
)
from core.database import get_db
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

router = APIRouter()


@router.post("", response_model=BaseResponse[DeliveryNoteResponse], status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[DeliveryNoteResponse]:
    """
    Create a new delivery note.
    
    Ingests a delivery note from ERP or OCR processing.
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
    
    # Create DN
    dn = DeliveryNote(
        vendor_id=dn_data.vendor_id,
        vendor_name=dn_data.vendor_name,
        po_id=dn_data.po_id,
        dn_number=dn_data.dn_number,
        dn_date=dn_data.dn_date,
        received_date=dn_data.received_date,
        status=DeliveryNoteStatus.CONFIRMED,
        total_amount=dn_data.total_amount,
        currency=dn_data.currency,
        source=dn_data.source,
        source_reference=dn_data.source_reference,
        carrier=dn_data.carrier,
        tracking_number=dn_data.tracking_number,
        number_of_packages=dn_data.number_of_packages,
        notes=dn_data.notes,
        received_by=dn_data.received_by,
        condition=dn_data.condition,
    )
    
    db.add(dn)
    await db.flush()
    
    # Create DN lines
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            dn_id=dn.id,
            po_line_id=line_data.po_line_id,
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            vendor_sku=line_data.vendor_sku,
            quantity_delivered=line_data.quantity_delivered,
            quantity_invoiced=0,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(dn)
    
    return BaseResponse(
        success=True,
        message="Delivery note created successfully",
        data=DeliveryNoteResponse.model_validate(dn),
    )


@router.get("", response_model=BaseResponse[PaginatedResponse[DeliveryNoteResponse]])
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = None,
    status: DeliveryNoteStatus | None = None,
    po_id: UUID | None = None,
) -> BaseResponse[PaginatedResponse[DeliveryNoteResponse]]:
    """
    List delivery notes with pagination and filtering.
    """
    # Build query
    query = select(DeliveryNote).where(DeliveryNote.is_deleted == False)
    count_query = select(func.count(DeliveryNote.id)).where(DeliveryNote.is_deleted == False)
    
    # Apply filters
    if vendor_id:
        query = query.where(DeliveryNote.vendor_id == vendor_id)
        count_query = count_query.where(DeliveryNote.vendor_id == vendor_id)
    
    if status:
        query = query.where(DeliveryNote.status == status)
        count_query = count_query.where(DeliveryNote.status == status)
    
    if po_id:
        query = query.where(DeliveryNote.po_id == po_id)
        count_query = count_query.where(DeliveryNote.po_id == po_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(DeliveryNote.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    dns_list = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return BaseResponse(
        success=True,
        data=PaginatedResponse(
            items=[DeliveryNoteResponse.model_validate(dn) for dn in dns_list],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    )


@router.get("/{dn_id}", response_model=BaseResponse[DeliveryNoteResponse])
async def get_delivery_note(
    dn_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[DeliveryNoteResponse]:
    """
    Get delivery note by ID.
    """
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False)
    )
    dn = result.scalar_one_or_none()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note with ID '{dn_id}' not found",
        )
    
    return BaseResponse(
        success=True,
        data=DeliveryNoteResponse.model_validate(dn),
    )
