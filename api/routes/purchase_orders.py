// api/routes/purchase_orders.py
"""Purchase Order routes."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from api.deps import get_current_user, require_role
from api.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderDetailResponse,
)
from core.database import get_db
from models.user import User
from models.purchase_order import PurchaseOrder, PurchaseOrderLine

router = APIRouter()


@router.get("/", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PurchaseOrder]:
    """
    List all purchase orders with optional filtering.
    """
    query = db.query(PurchaseOrder)
    
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    return query.offset(skip).limit(limit).all()


@router.get("/{po_id}", response_model=PurchaseOrderDetailResponse)
def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrder:
    """
    Get a purchase order by ID with all lines.
    """
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.lines)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    return po


@router.post("/", response_model=PurchaseOrderDetailResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> PurchaseOrder:
    """
    Create a new purchase order with lines.
    """
    # Check for duplicate PO number
    existing = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == po_data.po_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order with number '{po_data.po_number}' already exists",
        )
    
    # Create PO
    po_dict = po_data.model_dump(exclude={"lines"})
    po = PurchaseOrder(**po_dict)
    
    # Create lines
    for line_data in po_data.lines:
        line_dict = line_data.model_dump()
        line = PurchaseOrderLine(**line_dict)
        line.calculate_totals()
        po.lines.append(line)
    
    # Calculate totals
    po.calculate_totals()
    
    db.add(po)
    db.commit()
    db.refresh(po)
    
    return po


@router.patch("/{po_id}", response_model=PurchaseOrderDetailResponse)
def update_purchase_order(
    po_id: UUID,
    po_data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> PurchaseOrder:
    """
    Update a purchase order.
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    
    if po.status == "CLOSED" or po.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a closed or cancelled purchase order",
        )
    
    update_data = po_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)
    
    db.commit()
    db.refresh(po)
    
    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    """
    Delete a purchase order.
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )
    
    if po.status != "OPEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete open purchase orders",
        )
    
    db.delete(po)
    db.commit()
