// src/api/purchase_orders.py
"""Purchase Order API routes."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.models.user import User
from src.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineCreate,
)
from src.api.deps import get_current_user
from src.services.balance_service import BalanceService


router = APIRouter(prefix="/purchase-orders", tags=["purchase_orders"])


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> PurchaseOrder:
    """Create a new Purchase Order."""
    # Check for duplicate PO number
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase Order with number {po_data.po_number} already exists"
        )
    
    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        currency=po_data.currency,
        total_amount=po_data.total_amount,
        order_date=po_data.order_date,
        expected_date=po_data.expected_date,
        status="OPEN"
    )
    
    db.add(po)
    await db.flush()
    
    # Create lines
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            purchase_order_id=po.id,
            line_number=line_data.line_number,
            sku=line_data.sku,
            description=line_data.description,
            quantity_ordered=line_data.quantity_ordered,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(po)
    
    # Create initial balance entry
    await BalanceService.create_initial_balance(
        db,
        "purchase_order",
        po.id,
        po.total_amount,
        po.currency,
        f"PO {po.po_number} created"
    )
    
    return po


@router.get("/", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: str | None = None,
    status: str | None = None,
    po_number: str | None = None,
    _: User = Depends(get_current_user)
) -> PurchaseOrderListResponse:
    """List all Purchase Orders with pagination."""
    query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
    
    # Apply filters
    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if po_number:
        query = query.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(PurchaseOrder)
    if supplier_id:
        count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        count_query = count_query.where(PurchaseOrder.status == status)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(PurchaseOrder.created_at.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PurchaseOrderListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> PurchaseOrder:
    """Get a Purchase Order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    return po


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: UUID,
    po_data: PurchaseOrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> PurchaseOrder:
    """Update a Purchase Order."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    # Update fields
    update_data = po_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)
    
    await db.commit()
    await db.refresh(po)
    
    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> None:
    """Soft delete a Purchase Order."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    from datetime import datetime, timezone
    po.deleted_at = datetime.now(timezone.utc)
    await db.commit()
