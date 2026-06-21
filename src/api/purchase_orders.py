// src/api/purchase_orders.py
"""
Purchase Order API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from decimal import Decimal

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse
)

router = APIRouter()


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new Purchase Order"""
    # Check for duplicate PO number
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase Order number already exists"
        )
    
    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        supplier_code=po_data.supplier_code,
        po_date=po_data.po_date,
        expected_delivery_date=po_data.expected_delivery_date,
        currency=po_data.currency,
        notes=po_data.notes,
        terms_and_conditions=po_data.terms_and_conditions,
        created_by=current_user["user_id"]
    )
    
    # Calculate total from line items
    total_amount = Decimal("0")
    
    for line_data in po_data.line_items:
        line_amount = line_data.quantity * line_data.unit_price
        tax_amount = line_amount * line_data.tax_rate
        
        line = PurchaseOrderLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=tax_amount
        )
        po.line_items.append(line)
        total_amount += line_amount + tax_amount
    
    po.total_amount = total_amount
    
    db.add(po)
    await db.commit()
    await db.refresh(po)
    
    return po


@router.get("/", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List Purchase Orders with filtering and pagination"""
    # Build query
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
    
    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if search:
        query = query.where(
            PurchaseOrder.po_number.ilike(f"%{search}%") |
            PurchaseOrder.supplier_name.ilike(f"%{search}%")
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Get paginated results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(PurchaseOrder.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PurchaseOrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get Purchase Order by ID"""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.is_deleted == False
        )
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    return po


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: str,
    po_data: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update Purchase Order"""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.is_deleted == False
        )
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    # Only allow updates to certain fields
    update_data = po_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)
    
    await db.commit()
    await db.refresh(po)
    
    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete Purchase Order"""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.is_deleted == False
        )
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    po.is_deleted = True
    await db.commit()
