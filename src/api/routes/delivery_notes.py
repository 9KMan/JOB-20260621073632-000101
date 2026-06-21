// src/api/routes/delivery_notes.py
"""Delivery Note API routes."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.deps import DBSession, CurrentUser
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.user import User

router = APIRouter()


# Pydantic Schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line."""

    line_number: int
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity_delivered: Decimal = Field(ge=0)
    quantity_accepted: Decimal = Field(ge=0)
    quantity_rejected: Decimal = Field(ge=0, default=Decimal("0"))
    unit_of_measure: str = "EA"


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating Delivery Note line."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note line response."""

    id: str

    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""

    dn_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: str
    purchase_order_id: Optional[str] = None
    po_number: Optional[str] = None
    delivery_date: date
    currency: str = "USD"
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating Delivery Note."""

    subtotal: Decimal
    total_amount: Decimal
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating Delivery Note."""

    status: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""

    id: str
    subtotal: Decimal
    total_amount: Decimal
    status: str
    is_deleted: bool
    created_at: str
    updated_at: str
    lines: List[DeliveryNoteLineResponse] = []

    class Config:
        from_attributes = True


class DeliveryNoteListResponse(BaseModel):
    """Schema for Delivery Note list response."""

    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=DeliveryNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_in: DeliveryNoteCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> DeliveryNote:
    """Create a new Delivery Note."""
    # Check if DN number already exists
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_in.dn_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery Note {dn_in.dn_number} already exists",
        )

    # Create Delivery Note
    dn = DeliveryNote(
        dn_number=dn_in.dn_number,
        supplier_id=uuid.UUID(dn_in.supplier_id),
        supplier_name=dn_in.supplier_name,
        supplier_code=dn_in.supplier_code,
        purchase_order_id=uuid.UUID(dn_in.purchase_order_id) if dn_in.purchase_order_id else None,
        po_number=dn_in.po_number,
        delivery_date=dn_in.delivery_date,
        subtotal=dn_in.subtotal,
        total_amount=dn_in.total_amount,
        currency=dn_in.currency,
        delivery_address=dn_in.delivery_address,
        notes=dn_in.notes,
        status="DELIVERED",
    )
    db.add(dn)
    await db.flush()

    # Create lines
    for line_in in dn_in.lines:
        line = DeliveryNoteLine(
            delivery_note_id=dn.id,
            line_number=line_in.line_number,
            product_code=line_in.product_code,
            product_name=line_in.product_name,
            description=line_in.description,
            quantity_delivered=line_in.quantity_delivered,
            quantity_accepted=line_in.quantity_accepted,
            quantity_rejected=line_in.quantity_rejected,
            unit_of_measure=line_in.unit_of_measure,
        )
        db.add(line)

    await db.commit()
    await db.refresh(dn)

    return dn


@router.get("", response_model=DeliveryNoteListResponse)
async def list_delivery_notes(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_code: Optional[str] = None,
    status: Optional[str] = None,
    dn_number: Optional[str] = None,
    po_number: Optional[str] = None,
) -> dict:
    """List Delivery Notes with pagination."""
    query = select(DeliveryNote).where(DeliveryNote.is_deleted == False)

    if supplier_code:
        query = query.where(DeliveryNote.supplier_code == supplier_code)
    if status:
        query = query.where(DeliveryNote.status == status)
    if dn_number:
        query = query.where(DeliveryNote.dn_number.ilike(f"%{dn_number}%"))
    if po_number:
        query = query.where(DeliveryNote.po_number == po_number)

    # Get total count
    count_result = await db.execute(
        select(DeliveryNote.id).where(DeliveryNote.is_deleted == False)
    )
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.options(selectinload(DeliveryNote.lines))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(DeliveryNote.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(
    dn_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> DeliveryNote:
    """Get a Delivery Note by ID."""
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False)
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery Note not found",
        )

    return dn


@router.patch("/{dn_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: uuid.UUID,
    dn_in: DeliveryNoteUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> DeliveryNote:
    """Update a Delivery Note."""
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False)
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery Note not found",
        )

    update_data = dn_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dn, field, value)

    await db.commit()
    await db.refresh(dn)

    return dn


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_note(
    dn_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft delete a Delivery Note."""
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False)
    )
    dn = result.scalar_one_or_none()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery Note not found",
        )

    dn.is_deleted = True
    dn.deleted_at = date.today()
    await db.commit()
