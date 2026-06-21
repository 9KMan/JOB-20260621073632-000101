# app/api/purchase_orders.py
"""Purchase Order API endpoints."""
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
)

router = APIRouter()


def calculate_po_totals(po: PurchaseOrder) -> None:
    """Calculate PO subtotal, tax, and total amounts."""
    subtotal = Decimal("0")
    tax_amount = Decimal("0")
    for line in po.lines:
        line.calculate_line_total()
        line_total = line.quantity * line.unit_price
        subtotal += line_total
        tax_amount += line_total * line.tax_rate
    po.subtotal = subtotal
    po.tax_amount = tax_amount
    po.total_amount = subtotal + tax_amount + po.shipping_cost


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderResponse:
    """Create a new purchase order with line items."""
    # Check if PO number already exists
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase Order with number '{po_data.po_number}' already exists",
        )

    # Create PO
    po_dict = po_data.model_dump(exclude={"lines"})
    po = PurchaseOrder(**po_dict)

    # Create lines
    for line_data in po_data.lines:
        line = PurchaseOrderLine(**line_data.model_dump())
        line.calculate_line_total()
        po.lines.append(line)

    # Calculate totals
    calculate_po_totals(po)

    db.add(po)
    await db.commit()
    await db.refresh(po)

    # Reload with lines
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po.id)
    )
    po = result.scalar_one()

    return PurchaseOrderResponse.model_validate(po)


@router.get("/", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    po_number: Optional[str] = Query(None, description="Search by PO number"),
) -> PurchaseOrderListResponse:
    """List all purchase orders with pagination and filtering."""
    query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
    count_query = select(func.count(PurchaseOrder.id))

    # Apply filters
    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
        count_query = count_query.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)
    if po_number:
        po_filter = PurchaseOrder.po_number.ilike(f"%{po_number}%")
        query = query.where(po_filter)
        count_query = count_query.where(po_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(PurchaseOrder.created_at.desc())

    result = await db.execute(query)
    pos = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PurchaseOrderListResponse(
        items=[PurchaseOrderResponse.model_validate(po) for po in pos],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderResponse:
    """Get a purchase order by ID with line items."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order with ID '{po_id}' not found",
        )
    return PurchaseOrderResponse.model_validate(po)


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: str,
    po_data: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderResponse:
    """Update a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order with ID '{po_id}' not found",
        )

    # Check if PO is in editable status
    if po.status not in [POStatus.DRAFT.value, POStatus.SUBMITTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update PO in '{po.status}' status",
        )

    # Update fields
    update_data = po_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)

    await db.commit()
    await db.refresh(po)

    return PurchaseOrderResponse.model_validate(po)


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a purchase order (soft delete by setting status to cancelled)."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order with ID '{po_id}' not found",
        )

    if po.status not in [POStatus.DRAFT.value, POStatus.SUBMITTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete PO in '{po.status}' status",
        )

    po.status = POStatus.CANCELLED.value
    await db.commit()
