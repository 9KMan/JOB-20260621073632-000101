// api/v1/purchase_orders.py
"""Purchase Order API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from models.enums import PurchaseOrderStatus
from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderDetailResponse,
    PaginatedResponse,
    PaginationMeta,
)

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new purchase order",
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: DB,
) -> PurchaseOrder:
    """Ingest a new purchase order from ERP system.
    
    Creates a new PO with optional line items.
    """
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order with number {po_data.po_number} already exists",
        )
    
    # Create purchase order
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        order_date=po_data.order_date,
        delivery_date=po_data.delivery_date,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        status=PurchaseOrderStatus.APPROVED,
        notes=po_data.notes,
        erp_reference=po_data.erp_reference,
        is_anchored=False,
    )
    db.add(po)
    await db.flush()
    
    # Create line items
    for item_data in po_data.line_items:
        line_item = PurchaseOrderLineItem(
            po_id=po.id,
            line_number=item_data.line_number,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            amount=item_data.amount,
            uom=item_data.uom,
            tax_code=item_data.tax_code,
            delivery_date=item_data.delivery_date,
        )
        db.add(line_item)
    
    await db.commit()
    await db.refresh(po)
    
    return po


@router.get(
    "",
    response_model=PaginatedResponse[PurchaseOrderResponse],
    summary="List all purchase orders",
)
async def list_purchase_orders(
    db: DB,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    supplier_id: str | None = Query(None, description="Filter by supplier"),
    status: PurchaseOrderStatus | None = Query(None, description="Filter by status"),
    is_anchored: bool | None = Query(None, description="Filter by anchored status"),
    from_date: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
) -> PaginatedResponse[PurchaseOrderResponse]:
    """List all purchase orders with optional filters and pagination."""
    # Build base query
    query = select(PurchaseOrder)
    count_query = select(func.count(PurchaseOrder.id))
    
    # Apply filters
    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
        count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)
    if is_anchored is not None:
        query = query.where(PurchaseOrder.is_anchored == is_anchored)
        count_query = count_query.where(PurchaseOrder.is_anchored == is_anchored)
    if from_date:
        query = query.where(PurchaseOrder.order_date >= from_date)
        count_query = count_query.where(PurchaseOrder.order_date >= from_date)
    if to_date:
        query = query.where(PurchaseOrder.order_date <= to_date)
        count_query = count_query.where(PurchaseOrder.order_date <= to_date)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(PurchaseOrder.created_at.desc())
    
    result = await db.execute(query)
    pos = result.scalars().all()
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size
    meta = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    
    return PaginatedResponse(data=list(pos), meta=meta)


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderDetailResponse,
    summary="Get purchase order details",
)
async def get_purchase_order(
    po_id: UUID,
    db: DB,
) -> PurchaseOrder:
    """Get detailed purchase order information including line items."""
    query = (
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.line_items))
        .where(PurchaseOrder.id == po_id)
    )
    result = await db.execute(query)
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found",
        )
    
    return po


@router.patch(
    "/{po_id}/anchor",
    response_model=PurchaseOrderResponse,
    summary="Mark purchase order as anchored",
)
async def anchor_purchase_order(
    po_id: UUID,
    db: DB,
) -> PurchaseOrder:
    """Mark a purchase order as anchored for matching."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with id {po_id} not found",
        )
    
    po.is_anchored = True
    await db.commit()
    await db.refresh(po)
    
    return po
