// src/api/v1/endpoints/purchase_orders.py
"""Purchase Order endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import DbSession
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderLineCreate,
    PurchaseOrderLineResponse,
)
from src.schemas.common import PaginationParams, MessageResponse

router = APIRouter()


@router.get("/", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    db: DbSession,
    pagination: PaginationParams = Query(),
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    po_number: Optional[str] = None,
):
    """List all purchase orders with filtering and pagination."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if po_number:
        query = query.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = query.order_by(PurchaseOrder.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.limit)
    query = query.options(selectinload(PurchaseOrder.lines))

    result = await db.execute(query)
    items = result.scalars().all()

    return PurchaseOrderListResponse.create(
        items=[PurchaseOrderResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    db: DbSession,
    data: PurchaseOrderCreate,
):
    """Create a new purchase order."""
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order with number {data.po_number} already exists",
        )

    # Create PO
    po = PurchaseOrder(
        po_number=data.po_number,
        supplier_id=data.supplier_id,
        supplier_name=data.supplier_name,
        supplier_code=data.supplier_code,
        order_date=data.order_date,
        expected_delivery_date=data.expected_delivery_date,
        currency=data.currency,
        subtotal=data.subtotal,
        tax_amount=data.tax_amount,
        total_amount=data.total_amount,
        status=data.status,
        notes=data.notes,
    )

    # Add lines
    for line_data in data.lines:
        line = PurchaseOrderLine(
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            expected_delivery_date=line_data.expected_delivery_date,
            notes=line_data.notes,
        )
        po.lines.append(line)

    db.add(po)
    await db.flush()
    await db.refresh(po)

    return PurchaseOrderResponse.model_validate(po)


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    db: DbSession,
    po_id: UUID,
):
    """Get a purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .where(PurchaseOrder.is_deleted == False)
        .options(selectinload(PurchaseOrder.lines))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    return PurchaseOrderResponse.model_validate(po)


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    db: DbSession,
    po_id: UUID,
    data: PurchaseOrderUpdate,
):
    """Update a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .where(PurchaseOrder.is_deleted == False)
        .options(selectinload(PurchaseOrder.lines))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)

    await db.flush()
    await db.refresh(po)

    return PurchaseOrderResponse.model_validate(po)


@router.delete("/{po_id}", response_model=MessageResponse)
async def delete_purchase_order(
    db: DbSession,
    po_id: UUID,
):
    """Soft delete a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .where(PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    from datetime import datetime, timezone
    po.is_deleted = True
    po.deleted_at = datetime.now(timezone.utc)

    await db.flush()

    return MessageResponse(message="Purchase order deleted successfully")


@router.post("/{po_id}/approve", response_model=PurchaseOrderResponse)
async def approve_purchase_order(
    db: DbSession,
    po_id: UUID,
):
    """Approve a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .where(PurchaseOrder.is_deleted == False)
        .options(selectinload(PurchaseOrder.lines))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    if po.status != POStatus.SUBMITTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve purchase order in status: {po.status}",
        )

    from datetime import datetime, timezone
    po.status = POStatus.APPROVED.value
    po.approved_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(po)

    return PurchaseOrderResponse.model_validate(po)


@router.post("/{po_id}/close", response_model=PurchaseOrderResponse)
async def close_purchase_order(
    db: DbSession,
    po_id: UUID,
):
    """Close a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .where(PurchaseOrder.is_deleted == False)
        .options(selectinload(PurchaseOrder.lines))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    from datetime import datetime, timezone
    po.status = POStatus.CLOSED.value
    po.closed_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(po)

    return PurchaseOrderResponse.model_validate(po)
