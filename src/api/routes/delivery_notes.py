// src/api/routes/delivery_notes.py
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models.user import User
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.api.routes.auth import get_current_user
from src.api.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteListResponse
)

router = APIRouter(prefix="/delivery-notes", tags=["Delivery Notes"])


@router.post("/", response_model=DeliveryNoteResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new delivery note."""
    existing_dn = db.query(DeliveryNote).filter(
        DeliveryNote.dn_number == dn_data.dn_number
    ).first()
    
    if existing_dn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery note with number {dn_data.dn_number} already exists"
        )
    
    # Calculate totals
    line_items = []
    subtotal = 0
    tax_total = 0
    
    for line_data in dn_data.line_items:
        line_total = line_data.quantity * line_data.unit_price
        tax_amount = line_total * line_data.tax_rate
        subtotal += line_total
        tax_total += tax_amount
        
        line_items.append(DeliveryNoteLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=tax_amount,
            matched_po_line_id=line_data.matched_po_line_id,
            created_by=current_user.id
        ))
    
    delivery_note = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        supplier_code=dn_data.supplier_code,
        delivery_date=dn_data.delivery_date,
        received_date=dn_data.received_date,
        subtotal=subtotal,
        tax_amount=tax_total,
        total_amount=subtotal + tax_total,
        currency=dn_data.currency,
        notes=dn_data.notes,
        carrier_info=dn_data.carrier_info,
        status=DeliveryNoteStatus.RECEIVED,
        created_by=current_user.id
    )
    
    for line in line_items:
        delivery_note.line_items.append(line)
    
    db.add(delivery_note)
    db.commit()
    db.refresh(delivery_note)
    
    return delivery_note


@router.get("/", response_model=DeliveryNoteListResponse)
def list_delivery_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: UUID | None = None,
    status_filter: DeliveryNoteStatus | None = None,
    search: str | None = None
):
    """List all delivery notes with pagination."""
    query = db.query(DeliveryNote).options(joinedload(DeliveryNote.line_items))
    
    if supplier_id:
        query = query.filter(DeliveryNote.supplier_id == supplier_id)
    
    if status_filter:
        query = query.filter(DeliveryNote.status == status_filter)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            DeliveryNote.dn_number.ilike(search_term) |
            DeliveryNote.supplier_name.ilike(search_term)
        )
    
    total = query.count()
    items = query.order_by(DeliveryNote.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return DeliveryNoteListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
def get_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a delivery note by ID."""
    delivery_note = db.query(DeliveryNote).options(
        joinedload(DeliveryNote.line_items)
    ).filter(DeliveryNote.id == dn_id).first()
    
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found"
        )
    
    return delivery_note


@router.patch("/{dn_id}", response_model=DeliveryNoteResponse)
def update_delivery_note(
    dn_id: UUID,
    dn_data: DeliveryNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a delivery note."""
    delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found"
        )
    
    update_data = dn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(delivery_note, field, value)
    
    delivery_note.updated_by = current_user.id
    db.commit()
    db.refresh(delivery_note)
    
    return delivery_note


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a delivery note."""
    delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found"
        )
    
    db.delete(delivery_note)
    db.commit()
