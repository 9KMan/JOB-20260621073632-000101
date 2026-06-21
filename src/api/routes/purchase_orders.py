// src/api/routes/purchase_orders.py
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models.user import User
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.api.routes.auth import get_current_user
from src.api.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse
)

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new purchase order."""
    # Check for duplicate PO number
    existing_po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == po_data.po_number
    ).first()
    
    if existing_po:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order with number {po_data.po_number} already exists"
        )
    
    # Calculate totals
    line_items = []
    subtotal = 0
    tax_total = 0
    
    for line_data in po_data.line_items:
        line_total = line_data.quantity * line_data.unit_price
        tax_amount = line_total * line_data.tax_rate
        subtotal += line_total
        tax_total += tax_amount
        
        line_items.append(PurchaseOrderLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=tax_amount,
            expected_delivery_date=line_data.expected_delivery_date,
            notes=line_data.notes,
            created_by=current_user.id
        ))
    
    purchase_order = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        supplier_code=po_data.supplier_code,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        subtotal=subtotal,
        tax_amount=tax_total,
        total_amount=subtotal + tax_total,
        currency=po_data.currency,
        notes=po_data.notes,
        terms_and_conditions=po_data.terms_and_conditions,
        status=POStatus.OPEN,
        created_by=current_user.id
    )
    
    for line in line_items:
        purchase_order.line_items.append(line)
    
    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)
    
    return purchase_order


@router.get("/", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: UUID | None = None,
    status_filter: POStatus | None = None,
    search: str | None = None
):
    """List all purchase orders with pagination."""
    query = db.query(PurchaseOrder).options(joinedload(PurchaseOrder.line_items))
    
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    
    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            PurchaseOrder.po_number.ilike(search_term) |
            PurchaseOrder.supplier_name.ilike(search_term)
        )
    
    total = query.count()
    items = query.order_by(PurchaseOrder.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return PurchaseOrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a purchase order by ID."""
    purchase_order = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.line_items)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    return purchase_order


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    po_id: UUID,
    po_data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a purchase order."""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    update_data = po_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(purchase_order, field, value)
    
    purchase_order.updated_by = current_user.id
    db.commit()
    db.refresh(purchase_order)
    
    return purchase_order


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a purchase order (only if not matched)."""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    if purchase_order.status in [POStatus.PARTIALLY_MATCHED, POStatus.FULLY_MATCHED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a matched purchase order"
        )
    
    db.delete(purchase_order)
    db.commit()
