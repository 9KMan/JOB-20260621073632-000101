// src/api/routes/purchase_orders.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.api.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse
)

router = APIRouter()


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == po_data.po_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase Order with number {po_data.po_number} already exists"
        )
    
    subtotal = sum(line.unit_price * line.quantity for line in po_data.lines)
    tax_amount = subtotal * Decimal("0.10")
    total_amount = subtotal + tax_amount
    
    from decimal import Decimal
    db_po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_code=po_data.supplier_code,
        supplier_name=po_data.supplier_name,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        currency=po_data.currency,
        notes=po_data.notes,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=POStatus.SUBMITTED
    )
    db.add(db_po)
    db.flush()
    
    for line_data in po_data.lines:
        line_total = line_data.unit_price * line_data.quantity
        db_line = PurchaseOrderLine(
            purchase_order_id=db_po.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_total
        )
        db.add(db_line)
    
    db.commit()
    db.refresh(db_po)
    return db_po


@router.get("/", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    supplier_code: str = None,
    status: POStatus = None,
    db: Session = Depends(get_db)
):
    query = db.query(PurchaseOrder).options(joinedload(PurchaseOrder.lines))
    
    if supplier_code:
        query = query.filter(PurchaseOrder.supplier_code == supplier_code)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    pos = query.offset(skip).limit(limit).all()
    return pos


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(po_id: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.lines)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found"
        )
    return po


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: str,
    po_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found"
        )
    
    update_data = po_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)
    
    db.commit()
    db.refresh(po)
    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(po_id: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found"
        )
    
    db.delete(po)
    db.commit()
    return None
