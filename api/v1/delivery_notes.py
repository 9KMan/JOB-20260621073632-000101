# api/v1/delivery_notes.py
"""Delivery note endpoints."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    PaginatedResponse,
    PaginationMeta,
)
from core.database import get_db
from models.purchase_order import DeliveryNote, DeliveryNoteLine
from models.enums import DeliveryNoteStatus

router = APIRouter()


@router.post(
    "/",
    response_model=DeliveryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create delivery note",
    description="Ingest a new delivery note from warehouse.",
)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: AsyncSession = Depends(get_db),
) -> DeliveryNote:
    """
    Create a new delivery note with line items.
    """
    # Check for duplicate DN number
    stmt = select(DeliveryNote).where(
        DeliveryNote.dn_number == dn_data.dn_number,
        DeliveryNote.is_deleted == False,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery note {dn_data.dn_number} already exists",
        )

    # Create DN
    delivery_note = DeliveryNote(
        vendor_id=dn_data.vendor_id,
        vendor_name=dn_data.vendor_name,
        vendor_code=dn_data.vendor_code,
        purchase_order_id=dn_data.purchase_order_id,
        po_number=dn_data.po_number,
        dn_number=dn_data.dn_number,
        dn_date=dn_data.dn_date,
        received_date=dn_data.received_date,
        source_system=dn_data.source_system,
        notes=dn_data.notes,
        status=DeliveryNoteStatus.CONFIRMED,
    )

    db.add(delivery_note)
    await db.flush()

    # Create DN lines
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            dn_id=delivery_note.id,
            line_number=line_data.line_number,
            description=line_data.description,
            product_code=line_data.product_code,
            po_line_id=line_data.po_line_id,
            quantity_delivered=line_data.quantity_delivered,
            quantity_accepted=line_data.quantity_accepted,
            quantity_rejected=line_data.quantity_rejected,
        )
        db.add(line)

    await db.commit()
    await db.refresh(delivery_note)

    return delivery_note


@router.get(
    "/",
    response_model=PaginatedResponse[DeliveryNoteResponse],
    summary="List delivery notes",
    description="Get a paginated list of delivery notes.",
)
async def list_delivery_notes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_id: Optional[uuid.UUID] = Query(None, description="Filter by vendor"),
    purchase_order_id: Optional[uuid.UUID] = Query(None, description="Filter by PO"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List delivery notes with pagination and filters.
    """
    stmt = select(DeliveryNote).where(DeliveryNote.is_deleted == False)

    if vendor_id:
        stmt = stmt.where(DeliveryNote.vendor_id == vendor_id)
    if purchase_order_id:
        stmt = stmt.where(DeliveryNote.purchase_order_id == purchase_order_id)
    if status:
        stmt = stmt.where(DeliveryNote.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * per_page
    stmt = stmt.order_by(DeliveryNote.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(stmt)
    delivery_notes = result.scalars().all()

    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "data": delivery_notes,
        "meta": PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        ),
    }


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponse,
    summary="Get delivery note",
    description="Get a single delivery note by ID.",
)
async def get_delivery_note(
    dn_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DeliveryNote:
    """
    Get delivery note by ID with line items.
    """
    stmt = select(DeliveryNote).where(
        DeliveryNote.id == dn_id,
        DeliveryNote.is_deleted == False,
    )
    result = await db.execute(stmt)
    delivery_note = result.scalar_one_or_none()

    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery note {dn_id} not found",
        )

    return delivery_note
