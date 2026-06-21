// src/api/routes/delivery_notes.py
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.api.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse
)

router = APIRouter()


@router.post("/", response_model=DeliveryNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(DeliveryNote).filter(
        DeliveryNote.dn_number == dn_data.dn_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery Note with number {dn_data.dn_number} already exists"
        )
    
    subtotal = sum(line.unit_price * line.quantity for line in dn_data.lines) if dn_data.lines else Decimal("0.00")
    tax_amount = subtotal * Decimal("0.10")
    total_amount = subtotal + tax_amount
    
    db_dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_code=dn_data.supplier_code,
        supplier_name=dn_data.supplier_name,
        delivery_date=dn_data.delivery_date,
        purchase_order_id=dn_data.purchase_order_id,
        received_by=dn_data.received_by,
        currency=dn_data.currency,
        notes=dn_data.notes,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=DeliveryNoteStatus.SUBMITTED
    )
    db.add(db_dn)
    db.flush()
    
    for line_data in dn_data.lines:
        line_total = Decimal("0.00")
        db_line = DeliveryNoteLine(
            delivery_note_id=db_dn.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            line_total=line_total
        )
        db.add(db_line)
    
    db.commit()
    db.refresh(db_dn)
    return db_dn


@router.get("/", response_model=List[DeliveryNoteResponse])
async def list_delivery_notes(
    skip: int = 0,
    limit: int = 100,
    supplier_code: str = None,
    status: DeliveryNoteStatus = None,
    purchase_order_id: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(DeliveryNote).options(joinedload(DeliveryNote.lines))
    
    if supplier_code:
        query = query.filter(DeliveryNote.supplier_code == supplier_code)
    if status:
        query = query.filter(DeliveryNote.status == status)
    if purchase_order_id:
        query = query.filter(DeliveryNote.purchase_order_id == purchase_order_id)
    
    dns = query.offset(skip).limit(limit).all()
    return dns


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(dn_id: str, db: Session = Depends(get_db)):
    dn = db.query(DeliveryNote).options(
        joinedload(DeliveryNote.lines)
    ).filter(DeliveryNote.id == dn_id).first()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found"
        )
    return dn


@router.patch("/{dn_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: str,
    dn_update: DeliveryNoteUpdate,
    db: Session = Depends(get_db)
):
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found"
        )
    
    update_data = dn_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dn, field, value)
    
    db.commit()
    db.refresh(dn)
    return dn


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_note(dn_id: str, db: Session = Depends(get_db)):
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery Note {dn_id} not found"
        )
    
    db.delete(dn)
    db.commit()
    return None
