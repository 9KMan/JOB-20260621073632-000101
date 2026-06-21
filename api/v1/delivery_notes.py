# api/v1/delivery_notes.py
"""Delivery note endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreateSchema,
    DeliveryNoteListSchema,
    DeliveryNoteResponseSchema,
    PaginatedResponse,
)
from core.database import DbSession
from models import DeliveryNote, DeliveryNoteLine
from models.enums import DeliveryNoteStatus

router = APIRouter()


@router.post(
    "",
    response_model=DeliveryNoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new delivery note",
    description="Create a new delivery note with optional line items.",
)
async def create_delivery_note(
    dn_data: DeliveryNoteCreateSchema,
    session: DbSession,
) -> DeliveryNote:
    """Create a new delivery note."""
    # Check for duplicate DN number
    existing = await session.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note {dn_data.dn_number} already exists",
        )

    # Create delivery note
    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        po_number=dn_data.po_number,
        vendor_code=dn_data.vendor_code,
        vendor_name=dn_data.vendor_name,
        delivery_date=dn_data.delivery_date,
        received_date=dn_data.received_date,
        currency=dn_data.currency,
        total_amount=dn_data.total_amount,
        status=DeliveryNoteStatus.RECEIVED.value,
        source_system=dn_data.source_system,
        erp_dn_id=dn_data.erp_dn_id,
        metadata_json=dn_data.metadata,
    )

    session.add(dn)
    await session.flush()

    # Create line items
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            delivery_note_id=dn.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            po_line_id=line_data.po_line_id,
            status="received",
        )
        session.add(line)

    await session.commit()
    await session.refresh(dn)

    return dn


@router.get(
    "",
    response_model=PaginatedResponse[DeliveryNoteListSchema],
    summary="List delivery notes",
    description="Retrieve a paginated list of delivery notes.",
)
async def list_delivery_notes(
    session: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    vendor_code: str | None = None,
    po_number: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
) -> dict:
    """List delivery notes with pagination and filters."""
    # Build query
    query = select(DeliveryNote).where(DeliveryNote.deleted_at.is_(None))
    count_query = select(func.count(DeliveryNote.id)).where(
        DeliveryNote.deleted_at.is_(None)
    )

    if vendor_code:
        query = query.where(DeliveryNote.vendor_code == vendor_code)
        count_query = count_query.where(DeliveryNote.vendor_code == vendor_code)

    if po_number:
        query = query.where(DeliveryNote.po_number == po_number)
        count_query = count_query.where(DeliveryNote.po_number == po_number)

    if status_filter:
        query = query.where(DeliveryNote.status == status_filter)
        count_query = count_query.where(DeliveryNote.status == status_filter)

    # Get total count
    total = await session.scalar(count_query)
    total = total or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(DeliveryNote.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    delivery_notes = result.scalars().all()

    return {
        "items": delivery_notes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponseSchema,
    summary="Get delivery note by ID",
    description="Retrieve a single delivery note with line items.",
)
async def get_delivery_note(
    dn_id: str,
    session: DbSession,
) -> DeliveryNote:
    """Get delivery note by ID."""
    result = await session.execute(
        select(DeliveryNote).where(DeliveryNote.id == dn_id)
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note {dn_id} not found",
        )

    return dn


@router.patch(
    "/{dn_id}/status",
    response_model=DeliveryNoteResponseSchema,
    summary="Update delivery note status",
    description="Update the status of a delivery note.",
)
async def update_delivery_note_status(
    dn_id: str,
    new_status: str,
    session: DbSession,
) -> DeliveryNote:
    """Update delivery note status."""
    result = await session.execute(
        select(DeliveryNote).where(DeliveryNote.id == dn_id)
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note {dn_id} not found",
        )

    dn.status = new_status
    await session.commit()
    await session.refresh(dn)

    return dn
