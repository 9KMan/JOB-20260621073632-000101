# api/v1/delivery_notes.py
"""Delivery note endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    ErrorResponse,
)
from core.database import get_db
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

router = APIRouter()


@router.post(
    "",
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
    """Create a new delivery note with lines."""
    existing = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.dn_number == dn_data.dn_number,
            DeliveryNote.vendor_number == dn_data.vendor_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery Note {dn_data.dn_number} already exists for this vendor",
        )

    delivery_note = DeliveryNote(
        vendor_number=dn_data.vendor_number,
        vendor_name=dn_data.vendor_name,
        dn_number=dn_data.dn_number,
        dn_date=dn_data.dn_date,
        received_date=dn_data.received_date,
        total_amount=dn_data.total_amount,
        currency=dn_data.currency,
        status=DeliveryNoteStatus.CONFIRMED.value,
        notes=dn_data.notes,
        source_system=dn_data.source_system,
        po_number=dn_data.po_number,
        carrier=dn_data.carrier,
        tracking_number=dn_data.tracking_number,
    )

    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            po_line_id=line_data.po_line_id,
            item_number=line_data.item_number,
            uom=line_data.uom,
        )
        delivery_note.lines.append(line)

    db.add(delivery_note)
    await db.flush()
    await db.refresh(delivery_note)

    return DeliveryNoteResponse.model_validate(delivery_note)


@router.get(
    "",
    response_model=PaginatedResponse[DeliveryNoteResponse],
)
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    po_number: str | None = Query(None, alias="po_number", description="Filter by PO number"),
) -> PaginatedResponse[DeliveryNoteResponse]:
    """List all delivery notes with pagination and filters."""
    query = select(DeliveryNote).where(DeliveryNote.is_deleted == False)
    count_query = select(func.count(DeliveryNote.id)).where(DeliveryNote.is_deleted == False)

    if vendor_number:
        query = query.where(DeliveryNote.vendor_number == vendor_number)
        count_query = count_query.where(DeliveryNote.vendor_number == vendor_number)

    if status_filter:
        query = query.where(DeliveryNote.status == status_filter)
        count_query = count_query.where(DeliveryNote.status == status_filter)

    if po_number:
        query = query.where(DeliveryNote.po_number == po_number)
        count_query = count_query.where(DeliveryNote.po_number == po_number)

    query = query.offset(pagination.offset).limit(pagination.page_size)
    query = query.order_by(DeliveryNote.dn_date.desc())

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    delivery_notes_list = result.scalars().all()
    total = count_result.scalar() or 0

    return PaginatedResponse.create(
        items=[DeliveryNoteResponse.model_validate(dn) for dn in delivery_notes_list],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_delivery_note(
    dn_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNoteResponse:
    """Get a specific delivery note by ID."""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False
        )
    )
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found",
        )

    return DeliveryNoteResponse.model_validate(delivery_note)


@router.patch(
    "/{dn_id}/status",
    response_model=DeliveryNoteResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_delivery_note_status(
    dn_id: str,
    new_status: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeliveryNoteResponse:
    """Update delivery note status."""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False
        )
    )
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found",
        )

    try:
        DeliveryNoteStatus(new_status)
    except ValueError:
        valid_statuses = [s.value for s in DeliveryNoteStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid values: {valid_statuses}",
        )

    delivery_note.status = new_status
    await db.flush()
    await db.refresh(delivery_note)

    return DeliveryNoteResponse.model_validate(delivery_note)


@router.delete(
    "/{dn_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_delivery_note(
    dn_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Soft delete a delivery note."""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False
        )
    )
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found",
        )

    delivery_note.is_deleted = True
    delivery_note.deleted_at = func.now()
    await db.flush()

    return SuccessResponse(
        success=True,
        message=f"Delivery Note {dn_id} deleted successfully",
    )
