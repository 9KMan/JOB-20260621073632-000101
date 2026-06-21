# api/v1/purchase_orders.py
"""Purchase Order ingestion and list/get endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PaginatedResponse,
    SuccessResponse,
)
from core.database import get_db
from models import PurchaseOrder, POLine

router = APIRouter()


@router.post(
    "/",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new purchase order",
)
async def ingest_purchase_order(
    payload: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Ingest a new purchase order from ERP with line items."""
    # Check for duplicate
    existing = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.vendor_code == payload.vendor_code,
            PurchaseOrder.po_number == payload.po_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PO {payload.po_number} already exists for vendor {payload.vendor_code}",
        )

    po = PurchaseOrder(
        po_number=payload.po_number,
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        vendor_tax_id=payload.vendor_tax_id,
        currency=payload.currency,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        po_date=payload.po_date,
        expected_delivery_date=payload.expected_delivery_date,
        notes=payload.notes,
    )

    for line_payload in payload.lines:
        line = POLine(
            line_number=line_payload.line_number,
            description=line_payload.description,
            quantity_ordered=line_payload.quantity_ordered,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
        )
        po.lines.append(line)

    db.add(po)
    await db.flush()
    await db.refresh(po)
    return PurchaseOrderResponse.model_validate(po)


@router.get(
    "/",
    response_model=PaginatedResponse[PurchaseOrderResponse],
    summary="List purchase orders",
)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor_code: str | None = Query(None, description="Filter by vendor code"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PurchaseOrderResponse]:
    """List all purchase orders with optional filtering and pagination."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_active == True)  # noqa: E712

    if vendor_code:
        query = query.where(PurchaseOrder.vendor_code == vendor_code)
    if status_filter:
        query = query.where(PurchaseOrder.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    pos = result.scalars().all()

    items = [PurchaseOrderResponse.model_validate(po) for po in pos]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Get a single purchase order",
)
async def get_purchase_order(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrderResponse:
    """Retrieve a single purchase order by ID."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )
    return PurchaseOrderResponse.model_validate(po)
