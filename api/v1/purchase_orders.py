# api/v1/purchase_orders.py
"""Purchase Order endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PaginatedResponse,
    BaseResponse,
)
from core.database import get_db
from models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus

router = APIRouter()


@router.post("", response_model=BaseResponse[PurchaseOrderResponse], status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[PurchaseOrderResponse]:
    """
    Create a new purchase order.
    
    Ingests a PO from the ERP system.
    """
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order with number '{po_data.po_number}' already exists",
        )
    
    # Create PO
    po = PurchaseOrder(
        vendor_id=po_data.vendor_id,
        vendor_name=po_data.vendor_name,
        vendor_tax_id=po_data.vendor_tax_id,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        subtotal=po_data.subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        source=po_data.source,
        source_reference=po_data.source_reference,
        payment_terms=po_data.payment_terms,
        delivery_terms=po_data.delivery_terms,
        notes=po_data.notes,
        ship_to=po_data.ship_to,
        bill_to=po_data.bill_to,
        status=PurchaseOrderStatus.ACTIVE,
    )
    
    db.add(po)
    await db.flush()
    
    # Create PO lines
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            po_id=po.id,
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            vendor_sku=line_data.vendor_sku,
            category=line_data.category,
            quantity_ordered=line_data.quantity_ordered,
            quantity_received=Decimal("0.0000"),
            quantity_invoiced=Decimal("0.0000"),
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            remaining_quantity=line_data.quantity_ordered,
            remaining_amount=line_data.line_amount,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(po)
    
    return BaseResponse(
        success=True,
        message="Purchase order created successfully",
        data=PurchaseOrderResponse.model_validate(po),
    )


@router.get("", response_model=BaseResponse[PaginatedResponse[PurchaseOrderResponse]])
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = None,
    status: PurchaseOrderStatus | None = None,
    po_date_from: datetime | None = None,
    po_date_to: datetime | None = None,
) -> BaseResponse[PaginatedResponse[PurchaseOrderResponse]]:
    """
    List purchase orders with pagination and filtering.
    """
    # Build query
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
    count_query = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.is_deleted == False)
    
    # Apply filters
    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
        count_query = count_query.where(PurchaseOrder.vendor_id == vendor_id)
    
    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)
    
    if po_date_from:
        query = query.where(PurchaseOrder.po_date >= po_date_from.date())
        count_query = count_query.where(PurchaseOrder.po_date >= po_date_from.date())
    
    if po_date_to:
        query = query.where(PurchaseOrder.po_date <= po_date_to.date())
        count_query = count_query.where(PurchaseOrder.po_date <= po_date_to.date())
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    pos_list = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return BaseResponse(
        success=True,
        data=PaginatedResponse(
            items=[PurchaseOrderResponse.model_validate(po) for po in pos_list],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    )


@router.get("/{po_id}", response_model=BaseResponse[PurchaseOrderResponse])
async def get_purchase_order(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[PurchaseOrderResponse]:
    """
    Get purchase order by ID.
    """
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID '{po_id}' not found",
        )
    
    return BaseResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(po),
    )


@router.get("/{po_id}/balance", response_model=BaseResponse[dict])
async def get_po_balance(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[dict]:
    """
    Get balance summary for a purchase order.
    """
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID '{po_id}' not found",
        )
    
    # Calculate totals from lines
    total_ordered = Decimal("0.00")
    total_invoiced = Decimal("0.00")
    total_received = Decimal("0.00")
    remaining_amount = Decimal("0.00")
    
    for line in po.lines:
        total_ordered += line.quantity_ordered * line.unit_price
        total_invoiced += line.quantity_invoiced * line.unit_price
        total_received += line.quantity_received * line.unit_price
        remaining_amount += line.remaining_amount
    
    return BaseResponse(
        success=True,
        data={
            "po_id": str(po.id),
            "po_number": po.po_number,
            "total_ordered": total_ordered,
            "total_invoiced": total_invoiced,
            "total_received": total_received,
            "remaining_amount": remaining_amount,
            "currency": po.currency,
            "line_count": len(po.lines),
        },
    )
