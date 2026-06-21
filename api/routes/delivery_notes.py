// api/routes/delivery_notes.py
"""Delivery Note routes."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from api.deps import get_current_user, require_role
from api.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteDetailResponse,
)
from core.database import get_db
from models.user import User
from models.delivery_note import DeliveryNote, DeliveryNoteLine

router = APIRouter()


@router.get("/", response_model=List[DeliveryNoteResponse])
def list_delivery_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    po_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DeliveryNote]:
    """
    List all delivery notes with optional filtering.
    """
    query = db.query(DeliveryNote)
    
    if supplier_id:
        query = query.filter(DeliveryNote.supplier_id == supplier_id)
    if status:
        query = query.filter(DeliveryNote.status == status)
    if po_id:
        query = query.filter(DeliveryNote.po_id == po_id)
    
    return query.offset(skip).limit(limit).all()


@router.get("/{dn_id}", response_model=DeliveryNoteDetailResponse)
def get_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeliveryNote:
    """
    Get a delivery note by ID with all lines.
    """
    dn = db.query(DeliveryNote).options(
        joinedload(DeliveryNote.lines)
    ).filter(DeliveryNote.id == dn_id).first()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )
    return dn


@router.post("/", response_model=DeliveryNoteDetailResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> DeliveryNote:
    """
    Create a new delivery note with lines.
    """
    # Check for duplicate DN number
    existing = db.query(DeliveryNote).filter(
        DeliveryNote.dn_number == dn_data.dn_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery note with number '{dn_data.dn_number}' already exists",
        )
    
    # Create delivery note
    dn_dict = dn_data.model_dump(exclude={"lines"})
    dn = DeliveryNote(**dn_dict)
    
    # Create lines
    for line_data in dn_data.lines:
        line_dict = line_data.model_dump()
        line = DeliveryNoteLine(**line_dict)
        dn.lines.append(line)
    
    db.add(dn)
    db.commit()
    db.refresh(dn)
    
    return dn


@router.patch("/{dn_id}", response_model=DeliveryNoteDetailResponse)
def update_delivery_note(
    dn_id: UUID,
    dn_data: DeliveryNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> DeliveryNote:
    """
    Update a delivery note.
    """
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )
    
    update_data = dn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dn, field, value)
    
    db.commit()
    db.refresh(dn)
    
    return dn


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    """
    Delete a delivery note.
    """
    dn = db.query(DeliveryNote).filter(DeliveryNote.id == dn_id).first()
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )
    
    db.delete(dn)
    db.commit()
