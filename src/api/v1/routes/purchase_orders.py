# src/api/v1/routes/purchase_orders.py
"""Purchase Order routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.dependencies import get_current_active_user
from src.models.user import User
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.api.v1.schemas.purchase_orders import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderDetailResponse,
)

router = APIRouter()


@router.post("/", response_model=PurchaseOrderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PurchaseOrder:
    """Create a new purchase order."""
    # Check for duplicate PO number
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order {po_data.po_number} already exists",
        )

    # Calculate totals
    subtotal = sum(line.line_total for line in po_data.lines)
    tax_amount = sum(line.tax_amount for line in po_data.lines)
    total_amount = subtotal + tax_amount

    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        supplier_reference=po_data.supplier_reference,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        currency=po_data.currency,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        notes=po_data.notes,
    )

    # Add lines
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            expected_delivery_date=line_data.expected_delivery_date,
        )
        po.lines.append(line)

    db.add(po)
    await db.commit()
    await db.refresh(po)

    return po


@router.get("/", response_model=list[PurchaseOrderResponse])
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    supplier_id: str | None = None,
    status: str | None = None,
) -> list[PurchaseOrder]:
    """List all purchase orders with pagination."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_active == True)

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == status)

    query = query.offset(skip).limit(limit).order_by(PurchaseOrder.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{po_id}", response_model=PurchaseOrderDetailResponse)
async def get_purchase_order(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PurchaseOrder:
    """Get a purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    return po


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: UUID,
    po_data: PurchaseOrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PurchaseOrder:
    """Update a purchase order."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
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
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Soft delete a purchase order."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    po.is_active = False
    await db.commit()
