# api/v1/purchase_orders.py
"""Purchase order ingestion and list/get endpoints."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ErrorResponse,
    PurchaseOrderCreateSchema,
    PurchaseOrderListResponse,
    PurchaseOrderResponseSchema,
)
from core.database import get_db
from models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus

router = APIRouter()


@router.post(
    "/",
    response_model=PurchaseOrderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_purchase_order(
    po_data: PurchaseOrderCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """
    Ingest a new purchase order from ERP.
    
    Creates the PO header and line items.
    Initializes balance ledger entries for each line.
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

    # Create purchase order
    purchase_order = PurchaseOrder(
        vendor_id=po_data.vendor_id,
        vendor_name=po_data.vendor_name,
        vendor_address=po_data.vendor_address,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        currency=po_data.currency,
        total_amount=po_data.total_amount,
        tax_amount=po_data.tax_amount,
        status=PurchaseOrderStatus.APPROVED.value,
        notes=po_data.notes,
    )
    db.add(purchase_order)
    await db.flush()

    # Create PO lines
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            purchase_order_id=purchase_order.id,
            line_number=line_data.line_number,
            description=line_data.description,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            received_quantity=line_data.received_quantity,
            invoiced_quantity=line_data.invoiced_quantity,
            status="pending",
        )
        db.add(line)

    await db.commit()
    await db.refresh(purchase_order)

    return purchase_order


@router.get(
    "/",
    response_model=list[PurchaseOrderListResponse],
)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    from_date: Annotated[date | None, Query(alias="fromDate")] = None,
    to_date: Annotated[date | None, Query(alias="toDate")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[PurchaseOrder]:
    """List purchase orders with optional filtering and pagination."""
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)

    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if from_date:
        query = query.where(PurchaseOrder.po_date >= from_date)
    if to_date:
        query = query.where(PurchaseOrder.po_date <= to_date)

    query = query.offset((page - 1) * per_page).limit(per_page)
    query = query.order_by(PurchaseOrder.po_date.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponseSchema,
    responses={404: {"model": ErrorResponse}},
)
async def get_purchase_order(
    po_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """Get purchase order by ID with all line items."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID '{po_id}' not found",
        )

    return purchase_order


@router.get(
    "/number/{po_number}",
    response_model=PurchaseOrderResponseSchema,
    responses={404: {"model": ErrorResponse}},
)
async def get_purchase_order_by_number(
    po_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PurchaseOrder:
    """Get purchase order by PO number with all line items."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
    )
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with number '{po_number}' not found",
        )

    return purchase_order
