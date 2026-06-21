// src/api/delivery_notes.py
"""
Delivery Note API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from decimal import Decimal

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteListResponse
)

router = APIRouter()


@router.post("/", response_model=DeliveryNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new Delivery Note"""
    # Check for duplicate DN number
    result = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery Note number already exists"
        )
    
    # Create Delivery Note
    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        supplier_code=dn_data.supplier_code,
        dn_date=dn_data.dn_date,
        received_date=dn_data.received_date,
        currency=dn_data.currency,
        received_by=dn_data.received_by,
        warehouse_location=dn_data.warehouse_location,
        notes=dn_data.notes,
        created_by=current_user["user_id"]
    )
    
    # Calculate totals from line items
    subtotal = Decimal("0")
    
    for line_data in dn_data.line_items:
        line = DeliveryNoteLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            ordered_quantity=line_data.ordered_quantity,
            delivered_quantity=line_data.delivered_quantity,
            accepted_quantity=line_data.accepted_quantity,
            rejected_quantity=line_data.rejected_quantity,
            unit_of_measure=line_data.unit_of_measure,
            purchase_order_line_id=line_data.purchase_order_line_id
        )
        dn.line_items.append(line)
    
    # Calculate total (assuming unit price from ordered quantity context)
    for line_data in dn_data.line_items:
        # This would typically come from the linked PO line
        subtotal += line_data.delivered_quantity * Decimal("1.00")  # Placeholder
    
    dn.subtotal = subtotal
    dn.total_amount = subtotal
    
    db.add(dn)
    await db.commit()
    await db.refresh(dn)
    
    return dn


@router.get("/", response_model=DeliveryNoteListResponse)
async def list_delivery_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    purchase_order_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List Delivery Notes with filtering and pagination"""
    query = select(DeliveryNote).where(DeliveryNote.is_deleted == False)
    
    if supplier_id:
        query = query.where(DeliveryNote.supplier_id == supplier_id)
    if status:
        query = query.where(DeliveryNote.status == status)
    if purchase_order_id:
        query = query.where(DeliveryNote.purchase_order_id == purchase_order_id)
    if search:
        query = query.where(
            DeliveryNote.dn_number.ilike(f"%{search}%") |
            DeliveryNote.supplier_name.ilike(f"%{search}%")
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(DeliveryNote.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    
    return DeliveryNoteListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.get("/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(
    dn_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get Delivery Note by ID"""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id,
            DeliveryNote.is_deleted == False
        )
    )
    dn = result.scalar_one_or_none()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery Note not found"
        )
    
    return dn


@router.put("/{dn_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: str,
    dn_data: DeliveryNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update Delivery Note"""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id,
            DeliveryNote.is_deleted == False
        )
    )
    dn = result.scalar_one_or_none()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery Note not found"
        )
    
    update_data = dn_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dn, field, value)
    
    await db.commit()
    await db.refresh(dn)
    
    return dn


@router.delete("/{dn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_note(
    dn_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete Delivery Note"""
    result = await db.execute(
        select(DeliveryNote).where(
            DeliveryNote.id == dn_id,
            DeliveryNote.is_deleted == False
        )
    )
    dn = result.scalar_one_or_none()
    
    if not dn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery Note not found"
        )
    
    dn.is_deleted = True
    await db.commit()
