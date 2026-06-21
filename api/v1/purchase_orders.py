# api/v1/purchase_orders.py
"""Purchase order ingestion and CRUD endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PaginatedResponse,
    ErrorResponse,
)
from core.database import get_db
from models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus

router = APIRouter()


@router.post(
    "/",
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
    """Create a new purchase order with line items."""
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order with number {po_data.po_number} already exists",
        )

    purchase_order = PurchaseOrder(
        id=str(uuid4()),
        vendor_number=po_data.vendor_number,
        vendor_name=po_data.vendor_name,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        notes=po_data.notes,
        status=PurchaseOrderStatus.ACTIVE.value,
    )

    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            id=str(uuid4()),
            purchase_order_id=purchase_order.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            notes=line_data.notes,
        )
        purchase_order.lines.append(line)

    db.add(purchase_order)
    await db.flush()
    await db.refresh(purchase_order)

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.get(
    "/",
    response_model=PaginatedResponse[PurchaseOrderResponse],
)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status: str | None = Query(None, description="Filter by status"),
    po_number: str | None = Query(None, description="Filter by PO number"),
) -> PaginatedResponse[PurchaseOrderResponse]:
    """List all purchase orders with pagination and filtering."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_active == True)

    if vendor_number:
        query = query.where(PurchaseOrder.vendor_number == vendor_number)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if po_number:
        query = query.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(PurchaseOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    purchase_orders = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=[PurchaseOrderResponse.model_validate(po) for po in purchase_orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_purchase_order(
    po_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Get a specific purchase order by ID."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.get(
    "/by-number/{po_number}",
    response_model=PurchaseOrderResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_purchase_order_by_number(
    po_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Get a purchase order by PO number."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with number {po_number} not found",
        )

    return PurchaseOrderResponse.model_validate(purchase_order)


@router.patch(
    "/{po_id}/status",
    response_model=PurchaseOrderResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def update_purchase_order_status(
    po_id: str,
    status: str = Query(..., description="New status"),
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Update purchase order status."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    purchase_order.status = status
    purchase_order.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(purchase_order)

    return PurchaseOrderResponse.model_validate(purchase_order)
