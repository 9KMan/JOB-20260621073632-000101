// api/routes/delivery_notes.py
"""Delivery Note routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.security import get_current_active_user
from app.models.user import User
from app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from api.schemas.documents import (
    DeliveryNoteCreate,
    DeliveryNoteResponse,
    DeliveryNoteUpdate,
    DeliveryNoteLineResponse,
)

router = APIRouter()


@router.get("/", response_model=List[DeliveryNoteResponse])
async def list_delivery_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    po_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all delivery notes with pagination."""
    query = db.query(DeliveryNote).options(joinedload(DeliveryNote.lines))

    if supplier_id:
        query = query.filter(DeliveryNote.supplier_id == supplier_id)
    if po_id:
        query = query.filter(DeliveryNote.po_id == po_id)
    if status:
        query = query.filter(DeliveryNote.status == status)

    total = query.count()
    delivery_notes = (
        query.order_by(DeliveryNote.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return delivery_notes


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a delivery note by ID."""
    dn = (
        db.query(DeliveryNote)
        .options(joinedload(DeliveryNote.lines))
        .filter(DeliveryNote.id == dn_id)
        .first()
    )

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    return dn


@router.post("/", response_model=DeliveryNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new delivery note."""
    # Check for duplicate DN number
    existing = db.query(DeliveryNote).filter(DeliveryNote.dn_number == dn_data.dn_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery note number already exists",
        )

    # Create delivery note
    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        delivery_date=dn_data.delivery_date,
        received_date=dn_data.received_date,
        total_amount=dn_data.total_amount,
        currency=dn_data.currency,
        notes=dn_data.notes,
        po_id=dn_data.po_id,
        created_by=current_user.id,
    )
    db.add(dn)
    db.flush()

    # Create delivery note lines
    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            dn_id=dn.id,
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.quantity * line_data.unit_price,
            uom=line_data.uom,
        )
        db.add(line)

    db.commit()
    db.refresh(dn)

    return dn


@router.put("/{dn_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: UUID,
    dn_data: DeliveryNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a delivery note."""
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    # Update fields
    update_data = dn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dn, field, value)

    db.commit()
    db.refresh(dn)

    return dn


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a delivery note."""
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    db.delete(dn)
    db.commit()


@router.get("/{dn_id}/lines", response_model=List[DeliveryNoteLineResponse])
async def get_dn_lines(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all lines for a delivery note."""
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()

    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    return dn.lines
