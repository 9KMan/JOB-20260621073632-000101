// src/api/routes/purchase_orders.py
"""Purchase Order API routes."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.deps import DBSession, CurrentUser
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.user import User

router = APIRouter()


# Pydantic Schemas
class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line."""

    line_number: int
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity_ordered: Decimal = Field(ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""

    id: str
    line_total: Decimal
    quantity_received: Decimal

    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""

    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: str
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating Purchase Order."""

    subtotal: Decimal
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating Purchase Order."""

    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""

    id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_deleted: bool
    created_at: str
    updated_at: str
    lines: List[PurchaseOrderLineResponse] = []

    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    """Schema for Purchase Order list response."""

    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> PurchaseOrder:
    """Create a new Purchase Order."""
    # Check if PO number already exists
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_in.po_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase Order {po_in.po_number} already exists",
        )

    # Create PO
    po = PurchaseOrder(
        po_number=po_in.po_number,
        supplier_id=uuid.UUID(po_in.supplier_id),
        supplier_name=po_in.supplier_name,
        supplier_code=po_in.supplier_code,
        order_date=po_in.order_date,
        expected_delivery_date=po_in.expected_delivery_date,
        subtotal=po_in.subtotal,
        tax_amount=po_in.tax_amount,
        total_amount=po_in.total_amount,
        currency=po_in.currency,
        payment_terms=po_in.payment_terms,
        delivery_address=po_in.delivery_address,
        notes=po_in.notes,
        status="OPEN",
    )
    db.add(po)
    await db.flush()

    # Create lines
    for line_in in po_in.lines:
        line_total = line_in.quantity_ordered * line_in.unit_price
        line = PurchaseOrderLine(
            purchase_order_id=po.id,
            line_number=line_in.line_number,
            product_code=line_in.product_code,
            product_name=line_in.product_name,
            description=line_in.description,
            quantity_ordered=line_in.quantity_ordered,
            quantity_received=Decimal("0"),
            unit_of_measure=line_in.unit_of_measure,
            unit_price=line_in.unit_price,
            line_total=line_total,
            expected_delivery_date=line_in.expected_delivery_date,
        )
        db.add(line)

    await db.commit()
    await db.refresh(po)

    return po


@router.get("", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_code: Optional[str] = None,
    status: Optional[str] = None,
    po_number: Optional[str] = None,
) -> dict:
    """List Purchase Orders with pagination."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)

    if supplier_code:
        query = query.where(PurchaseOrder.supplier_code == supplier_code)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if po_number:
        query = query.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))

    # Get total count
    count_result = await db.execute(
        select(PurchaseOrder.id).where(PurchaseOrder.is_deleted == False)
    )
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.options(selectinload(PurchaseOrder.lines))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(PurchaseOrder.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> PurchaseOrder:
    """Get a Purchase Order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found",
        )

    return po


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: uuid.UUID,
    po_in: PurchaseOrderUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> PurchaseOrder:
    """Update a Purchase Order."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found",
        )

    update_data = po_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(po, field, value)

    await db.commit()
    await db.refresh(po)

    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    po_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft delete a Purchase Order."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found",
        )

    po.is_deleted = True
    po.deleted_at = date.today()
    await db.commit()
