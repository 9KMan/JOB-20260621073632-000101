# api/v1/purchase_orders.py
"""Purchase order endpoints for ingestion and retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    ErrorResponse,
)
from core.database import get_db
from models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus

router = APIRouter()


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Create a new purchase order with lines."""
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase Order {po_data.po_number} already exists",
        )

    purchase_order = PurchaseOrder(
        vendor_number=po_data.vendor_number,
        vendor_name=po_data.vendor_name,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        status=PurchaseOrderStatus.ACTIVE.value,
        notes=po_data.notes,
        source_system=po_data.source_system,
        department=po_data.department,
        cost_center=po_data.cost_center,
    )

    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            line_number=line_data.line_number,
            description=line_data.description,
            ordered_quantity=line_data.ordered_quantity,
            received_quantity=line_data.received_quantity,
            invoiced_quantity=line_data.invoiced_quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            delivery_date=line_data.delivery_date,
            item_number=line_data.item_number,
            uom=line_data.uom,
        )
        purchase_order.lines.append(line)

    db.add(purchase_order)
    await db.flush()
    await db.refresh(purchase_order)

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.get(
    "",
    response_model=PaginatedResponse[PurchaseOrderResponse],
)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    from_date: str | None = Query(None, alias="from_date", description="Filter from date"),
    to_date: str | None = Query(None, alias="to_date", description="Filter to date"),
) -> PaginatedResponse[PurchaseOrderResponse]:
    """List all purchase orders with pagination and filters."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
    count_query = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.is_deleted == False)

    if vendor_number:
        query = query.where(PurchaseOrder.vendor_number == vendor_number)
        count_query = count_query.where(PurchaseOrder.vendor_number == vendor_number)

    if status_filter:
        query = query.where(PurchaseOrder.status == status_filter)
        count_query = count_query.where(PurchaseOrder.status == status_filter)

    query = query.offset(pagination.offset).limit(pagination.page_size)
    query = query.order_by(PurchaseOrder.po_date.desc())

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    purchase_orders_list = result.scalars().all()
    total = count_result.scalar() or 0

    return PaginatedResponse.create(
        items=[PurchaseOrderResponse.model_validate(po) for po in purchase_orders_list],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_purchase_order(
    po_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Get a specific purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False
        )
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.get(
    "/by-number/{po_number}",
    response_model=PurchaseOrderResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_purchase_order_by_number(
    po_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Get a specific purchase order by PO number."""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_number, PurchaseOrder.is_deleted == False
        )
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_number} not found",
        )

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.patch(
    "/{po_id}/status",
    response_model=PurchaseOrderResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_purchase_order_status(
    po_id: str,
    new_status: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Update purchase order status."""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False
        )
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    try:
        PurchaseOrderStatus(new_status)
    except ValueError:
        valid_statuses = [s.value for s in PurchaseOrderStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid values: {valid_statuses}",
        )

    purchase_order.status = new_status
    await db.flush()
    await db.refresh(purchase_order)

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.delete(
    "/{po_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_purchase_order(
    po_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Soft delete a purchase order."""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False
        )
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    purchase_order.is_deleted = True
    purchase_order.deleted_at = func.now()
    await db.flush()

    return SuccessResponse(
        success=True,
        message=f"Purchase Order {po_id} deleted successfully",
    )
