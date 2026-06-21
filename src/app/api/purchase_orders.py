// src/app/api/purchase_orders.py
"""Purchase Order API routes."""
import uuid
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine, PO_STATUS
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
)
from app.api.deps import get_current_user


router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new Purchase Order."""
    # Check if PO number already exists
    stmt = select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase Order {po_data.po_number} already exists",
        )

    # Calculate totals
    subtotal = sum(line.unit_price * line.quantity for line in po_data.lines)
    tax_amount = Decimal("0")  # Tax can be calculated based on business rules
    total_amount = subtotal + tax_amount

    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        supplier_address=po_data.supplier_address,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        currency=po_data.currency,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        notes=po_data.notes,
        metadata=po_data.metadata,
        status=PO_STATUS.DRAFT,
    )

    db.add(po)
    await db.flush()

    # Create lines
    for line_data in po_data.lines:
        line_total = line_data.unit_price * line_data.quantity
        line = PurchaseOrderLine(
            purchase_order_id=po.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            product_description=line_data.product_description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_total,
            expected_delivery_date=line_data.expected_delivery_date,
            metadata=line_data.metadata,
        )
        db.add(line)

    await db.flush()
    await db.refresh(po)
    return po


@router.get("/", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all Purchase Orders with pagination."""
    conditions = []
    if supplier_id:
        conditions.append(PurchaseOrder.supplier_id == supplier_id)
    if status:
        try:
            status_enum = PO_STATUS[status.upper()]
            conditions.append(PurchaseOrder.status == status_enum)
        except KeyError:
            pass

    # Count total
    count_stmt = select(func.count(PurchaseOrder.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    # Get items
    offset = (page - 1) * page_size
    stmt = select(PurchaseOrder).options()
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.offset(offset).limit(page_size).order_by(PurchaseOrder.created_at.desc())

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size

    return PurchaseOrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a Purchase Order by ID."""
    stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    result = await db.execute(stmt)
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found",
        )

    return po


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: uuid.UUID,
    po_data: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a Purchase Order."""
    stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    result = await db.execute(stmt)
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found",
        )

    update_data = po_data.model_dump(exclude_unset=True)

    # Handle status enum
    if "status" in update_data and update_data["status"]:
        try:
            update_data["status"] = PO_STATUS[update_data["status"].upper()]
        except KeyError:
            del update_data["status"]

    for field, value in update_data.items():
        setattr(po, field, value)

    await db.flush()
    await db.refresh(po)
    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a Purchase Order."""
    stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    result = await db.execute(stmt)
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found",
        )

    await db.delete(po)
    await db.flush()
