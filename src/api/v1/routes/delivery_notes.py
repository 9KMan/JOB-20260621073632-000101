# src/api/v1/routes/delivery_notes.py
"""Delivery Note routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.dependencies import get_current_active_user
from src.models.user import User
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.api.v1.schemas.delivery_notes import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteDetailResponse,
)

router = APIRouter()


@router.post("/", response_model=DeliveryNoteDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DeliveryNote:
    """Create a new delivery note."""
    # Check for duplicate DN number
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery note {dn_data.dn_number} already exists",
        )

    # Calculate totals
    subtotal = sum(line.line_total for line in dn_data.lines)
    tax_amount = Decimal("0.00")  # Delivery notes typically don't have tax
    total_amount = subtotal + tax_amount

    from decimal import Decimal

    # Create Delivery Note
    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        supplier_reference=dn_data.supplier_reference,
        po_reference=dn_data.po_reference,
        delivery_date=dn_data.delivery_date,
        received_by=dn_data.received_by,
        currency=dn_data.currency,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        notes=dn_data.notes,
    )

    # Add lines
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            quantity_received=line_data.quantity_received,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            purchase_order_line_id=line_data.purchase_order_line_id,
        )
        dn.lines.append(line)

    db.add(dn)
    await db.commit()
    await db.refresh(dn)

    return dn


@router.get("/", response_model=list[DeliveryNoteResponse])
async def list_delivery_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    supplier_id: str | None = None,
    status: str | None = None,
) -> list[DeliveryNote]:
    """List all delivery notes with pagination."""
    query = select(DeliveryNote).where(DeliveryNote.is_active == True)

    if supplier_id:
        query = query.where(DeliveryNote.supplier_id == supplier_id)
    if status:
        query = query.where(DeliveryNote.status == status)

    query = query.offset(skip).limit(limit).order_by(DeliveryNote.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{dn_id}", response_model=DeliveryNoteDetailResponse)
async def get_delivery_note(
    dn_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DeliveryNote:
    """Get a delivery note by ID."""
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn_id)
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    return dn


@router.patch("/{dn_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: UUID,
    dn_data: DeliveryNoteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DeliveryNote:
    """Update a delivery note."""
    result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    # Update fields
    update_data = dn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dn, field, value)

    await db.commit()
    await db.refresh(dn)

    return dn


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_note(
    dn_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Soft delete a delivery note."""
    result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    dn.is_active = False
    await db.commit()
