// api/v1/purchase_orders.py
"""Purchase Order API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    SuccessResponse,
)
from core.database import get_db
from models.enums import PurchaseOrderStatus
from models.purchase_order import PurchaseOrder, PurchaseOrderLine

router = APIRouter()


@router.post(
    "/",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new purchase order",
    description="Create a new PO from ERP system with optional line items.",
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """Create a new purchase order."""
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order {po_data.po_number} already exists",
        )

    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        vendor_number=po_data.vendor_number,
        vendor_name=po_data.vendor_name,
        vendor_address=po_data.vendor_address,
        created_date=po_data.created_date,
        expected_delivery_date=po_data.expected_delivery_date,
        currency=po_data.currency,
        subtotal=po_data.subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=po_data.total_amount,
        description=po_data.description,
        payment_terms=po_data.payment_terms,
        shipping_terms=po_data.shipping_terms,
        source_system=po_data.source_system,
        external_ref=po_data.external_ref,
        status=PurchaseOrderStatus.ISSUED,
    )
    db.add(po)
    await db.flush()

    # Create line items
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            po_id=po.id,
            line_number=line_data.line_number,
            description=line_data.description,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            unit_of_measure=line_data.unit_of_measure,
            ordered_quantity=line_data.ordered_quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            expected_delivery_date=line_data.expected_delivery_date,
        )
        db.add(line)

    await db.commit()
    await db.refresh(po)
    return po


@router.get(
    "/",
    response_model=PurchaseOrderListResponse,
    summary="List purchase orders",
    description="Get a paginated list of POs with optional filters.",
)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_number: str | None = Query(None, description="Filter by vendor"),
    status: PurchaseOrderStatus | None = Query(None, description="Filter by status"),
    created_date_from: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    created_date_to: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
) -> PurchaseOrderListResponse:
    """Get paginated list of purchase orders."""
    # Build base query
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
    count_query = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.is_deleted == False)

    # Apply filters
    if vendor_number:
        query = query.where(PurchaseOrder.vendor_number == vendor_number)
        count_query = count_query.where(PurchaseOrder.vendor_number == vendor_number)
    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)
    if created_date_from:
        query = query.where(PurchaseOrder.created_date >= created_date_from)
        count_query = count_query.where(PurchaseOrder.created_date >= created_date_from)
    if created_date_to:
        query = query.where(PurchaseOrder.created_date <= created_date_to)
        count_query = count_query.where(PurchaseOrder.created_date <= created_date_to)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(PurchaseOrder.created_date.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    pos = result.scalars().all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PurchaseOrderListResponse(
        items=list(pos),
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Get purchase order by ID",
    description="Retrieve a single PO with its line items.",
)
async def get_purchase_order(
    po_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """Get a purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    return po


@router.get(
    "/by-number/{po_number}",
    response_model=PurchaseOrderResponse,
    summary="Get purchase order by PO number",
    description="Retrieve a PO by its number.",
)
async def get_purchase_order_by_number(
    po_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """Get a purchase order by its number."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.po_number == po_number, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_number} not found",
        )

    return po


@router.patch(
    "/{po_id}/status",
    response_model=PurchaseOrderResponse,
    summary="Update purchase order status",
    description="Update the status of a PO.",
)
async def update_po_status(
    po_id: uuid.UUID,
    status_update: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """Update purchase order status."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    new_status = status_update.get("status")
    if new_status:
        po.status = PurchaseOrderStatus(new_status)
        await db.commit()
        await db.refresh(po)

    return po


@router.delete(
    "/{po_id}",
    response_model=SuccessResponse,
    summary="Delete purchase order",
    description="Soft delete a purchase order.",
)
async def delete_purchase_order(
    po_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Soft delete a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    po.soft_delete()
    await db.commit()

    return SuccessResponse(message=f"Purchase order {po_id} deleted successfully")
