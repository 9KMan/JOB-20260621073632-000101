# api/v1/purchase_orders.py
"""Purchase order ingestion and list/get endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreateSchema,
    PurchaseOrderListSchema,
    PurchaseOrderResponseSchema,
    PaginatedResponse,
)
from core.database import DbSession
from models import PurchaseOrder, POLine
from models.enums import PurchaseOrderStatus

router = APIRouter()


@router.post(
    "",
    response_model=PurchaseOrderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new purchase order",
    description="Create a new purchase order with optional line items.",
)
async def create_purchase_order(
    po_data: PurchaseOrderCreateSchema,
    session: DbSession,
) -> PurchaseOrder:
    """Create a new purchase order."""
    # Check for duplicate PO number
    existing = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order {po_data.po_number} already exists",
        )

    # Create purchase order
    po = PurchaseOrder(
        po_number=po_data.po_number,
        vendor_code=po_data.vendor_code,
        vendor_name=po_data.vendor_name,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        currency=po_data.currency,
        subtotal=po_data.subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=po_data.total_amount,
        status=PurchaseOrderStatus.ACTIVE.value,
        source_system=po_data.source_system,
        erp_po_id=po_data.erp_po_id,
        metadata_json=po_data.metadata,
    )

    session.add(po)
    await session.flush()

    # Create line items
    for line_data in po_data.lines:
        line = POLine(
            po_id=po.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            status="active",
        )
        session.add(line)

    await session.commit()
    await session.refresh(po)

    return po


@router.get(
    "",
    response_model=PaginatedResponse[PurchaseOrderListSchema],
    summary="List purchase orders",
    description="Retrieve a paginated list of purchase orders.",
)
async def list_purchase_orders(
    session: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    vendor_code: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    po_date_from: str | None = None,
    po_date_to: str | None = None,
) -> dict:
    """List purchase orders with pagination and filters."""
    # Build query
    query = select(PurchaseOrder).where(PurchaseOrder.deleted_at.is_(None))
    count_query = select(func.count(PurchaseOrder.id)).where(
        PurchaseOrder.deleted_at.is_(None)
    )

    if vendor_code:
        query = query.where(PurchaseOrder.vendor_code == vendor_code)
        count_query = count_query.where(PurchaseOrder.vendor_code == vendor_code)

    if status_filter:
        query = query.where(PurchaseOrder.status == status_filter)
        count_query = count_query.where(PurchaseOrder.status == status_filter)

    # Get total count
    total = await session.scalar(count_query)
    total = total or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    purchase_orders = result.scalars().all()

    return {
        "items": purchase_orders,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponseSchema,
    summary="Get purchase order by ID",
    description="Retrieve a single purchase order with line items.",
)
async def get_purchase_order(
    po_id: str,
    session: DbSession,
) -> PurchaseOrder:
    """Get purchase order by ID."""
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    return po


@router.patch(
    "/{po_id}/status",
    response_model=PurchaseOrderResponseSchema,
    summary="Update purchase order status",
    description="Update the status of a purchase order.",
)
async def update_purchase_order_status(
    po_id: str,
    new_status: str,
    session: DbSession,
) -> PurchaseOrder:
    """Update purchase order status."""
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    po.status = new_status
    await session.commit()
    await session.refresh(po)

    return po
