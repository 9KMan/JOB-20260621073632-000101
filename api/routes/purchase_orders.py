// api/routes/purchase_orders.py
"""Purchase Order routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.security import get_current_active_user
from app.models.user import User
from app.models.purchase_order import PurchaseOrder, POLine
from api.schemas.documents import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    POLineResponse,
)

router = APIRouter()


@router.get("/", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all purchase orders with pagination."""
    query = db.query(PurchaseOrder).options(joinedload(PurchaseOrder.lines))

    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)

    total = query.count()
    orders = (
        query.order_by(PurchaseOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return orders


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a purchase order by ID."""
    po = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.lines))
        .filter(PurchaseOrder.id == po_id)
        .first()
    )

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    return po


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new purchase order."""
    # Check for duplicate PO number
    existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_data.po_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order number already exists",
        )

    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        notes=po_data.notes,
        created_by=current_user.id,
    )
    db.add(po)
    db.flush()

    # Create PO lines
    for line_data in po_data.lines:
        line = POLine(
            po_id=po.id,
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
    db.refresh(po)

    return po


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: UUID,
    po_data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    # Update fields
    update_data = po_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)

    db.commit()
    db.refresh(po)

    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    db.delete(po)
    db.commit()


@router.get("/{po_id}/lines", response_model=List[POLineResponse])
async def get_po_lines(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all lines for a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    return po.lines
