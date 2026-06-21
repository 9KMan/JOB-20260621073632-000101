// api/v1/delivery_notes.py
"""Delivery note endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    PaginatedResponse,
    PaginationParams,
    ErrorResponse,
)
from core.database import get_db_session
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeliveryNoteResponse:
    """
    Ingest a new delivery note from ERP/OCR.

    Creates a DN header and its associated line items.
    """
    # Check for duplicate DN
    existing = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.dn_number == dn_data.dn_number,
            DeliveryNote.is_deleted == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Delivery Note {dn_data.dn_number} already exists",
        )

    # Create DN
    dn = DeliveryNote(
        vendor_number=dn_data.vendor_number,
        vendor_name=dn_data.vendor_name,
        dn_number=dn_data.dn_number,
        dn_date=dn_data.dn_date,
        delivery_date=dn_data.delivery_date,
        dn_amount=dn_data.dn_amount,
        currency_code=dn_data.currency_code,
        po_id=uuid.UUID(dn_data.po_id) if dn_data.po_id else None,
        description=dn_data.description,
        carrier=dn_data.carrier,
        tracking_number=dn_data.tracking_number,
        status=DeliveryNoteStatus.CONFIRMED,
    )

    db.add(dn)
    await db.flush()

    # Create line items
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            dn_id=dn.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            po_line_id=uuid.UUID(line_data.po_line_id) if line_data.po_line_id else None,
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    pagination: Annotated[PaginationParams, Query()],
    vendor_number: Annotated[str | None, Query(description="Filter by vendor")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    po_id: Annotated[str | None, Query(description="Filter by PO ID")] = None,
) -> PaginatedResponse[DeliveryNoteResponse]:
    """
    List all delivery notes with pagination and filtering.
    """
    query = select(DeliveryNote).where(DeliveryNote.is_deleted == False)
    count_query = select(func.count(DeliveryNote.id)).where(DeliveryNote.is_deleted == False)

    if vendor_number:
        query = query.where(DeliveryNote.vendor_number == vendor_number)
        count_query = count_query.where(DeliveryNote.vendor_number == vendor_number)

    if status:
        query = query.where(DeliveryNote.status == status)
        count_query = count_query.where(DeliveryNote.status == status)

    if po_id:
        query = query.where(DeliveryNote.po_id == uuid.UUID(po_id))
        count_query = count_query.where(DeliveryNote.po_id == uuid.UUID(po_id))

    total = (await db.execute(count_query)).scalar_one()

    query = query.offset(pagination.offset).limit(pagination.limit)
    query = query.order_by(DeliveryNote.created_at.desc())

    result = await db.execute(query)
    dns = result.scalars().all()

    items = [DeliveryNoteResponse.model_validate(dn) for dn in dns]
    return PaginatedResponse.create(items, total, pagination)


@router.get(
    "/{dn_id}",
    response_model=DeliveryNoteResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_delivery_note(
    dn_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DeliveryNoteResponse:
    """
    Get a single delivery note by ID.
    """
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == uuid.UUID(dn_id),
            DeliveryNote.is_deleted == False,
        )
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found",
        )

    return DeliveryNoteResponse.model_validate(dn)
