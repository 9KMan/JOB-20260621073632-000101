# api/v1/delivery_notes.py
"""Delivery Note endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
)
from core.database import get_db
from models import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus

router = APIRouter()

DNDB = Annotated[AsyncSession, get_db]


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
    db: DNDB,
) -> DeliveryNoteResponse:
    """Create a new delivery note with line items."""
    # Check for duplicate DN number
    existing = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.dn_number == dn_data.dn_number,
            DeliveryNote.is_deleted == False,  # noqa: E712
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery Note {dn_data.dn_number} already exists",
        )

    # Create DN header
    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        vendor_id=dn_data.vendor_id,
        vendor_name=dn_data.vendor_name,
        po_number=dn_data.po_number,
        po_id=dn_data.po_id,
        dn_date=dn_data.dn_date,
        receipt_date=dn_data.receipt_date,
        gross_amount=dn_data.gross_amount,
        tax_amount=dn_data.tax_amount,
        net_amount=dn_data.net_amount,
        currency=dn_data.currency,
        status=DeliveryNoteStatus.RECEIVED.value,
        notes=dn_data.notes,
        carrier=dn_data.carrier,
        tracking_number=dn_data.tracking_number,
        source_system=dn_data.source_system,
        external_ref=dn_data.external_ref,
    )

    db.add(dn)
    await db.flush()

    # Create line items
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            dn_id=dn.id,
            line_number=line_data.line_number,
            description=line_data.description,
            part_number=line_data.part_number,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            net_amount=line_data.net_amount,
            po_line_id=line_data.po_line_id,
            received=True,
            received_date=dn_data.dn_date,
        )
        db.add(line)

    await db.commit()
    await db.refresh(dn)

    return DeliveryNoteResponse.model_validate(dn)


@router.get(
    "",
    response_model=PaginatedResponse[DeliveryNoteResponse],
)
async def list_delivery_notes(
    db: DNDB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = None,
    po_number: str | None = None,
    status: str | None = None,
) -> PaginatedResponse[DeliveryNoteResponse]:
    """List delivery notes with pagination and filters."""
    query = select(DeliveryNote).where(
        DeliveryNote.is_deleted == False  # noqa: E712
    )

    if vendor_id:
        query = query.where(DeliveryNote.vendor_id == vendor_id)
    if po_number:
        query = query.where(DeliveryNote.po_number == po_number)
    if status:
        query = query.where(DeliveryNote.status == status)

    # Count total
    from sqlalchemy import func

    count_query = select(func.count(DeliveryNote.id)).where(
        DeliveryNote.is_deleted == False  # noqa: E712
    )
    if vendor_id:
        count_query = count_query.where(DeliveryNote.vendor_id == vendor_id)
    if po_number:
        count_query = count_query.where(DeliveryNote.po_number == po_number)
    if status:
        count_query = count_query.where(DeliveryNote.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(DeliveryNote.created_at.desc())

    result = await db.execute(query)
    dns = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        data=[DeliveryNoteResponse.model_validate(dn) for dn in dns],
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_delivery_note(
    dn_id: UUID,
    db: DNDB,
) -> DeliveryNoteResponse:
    """Get delivery note by ID with line items."""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id,
            DeliveryNote.is_deleted == False,  # noqa: E712
        )
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found",
        )

    return DeliveryNoteResponse.model_validate(dn)
