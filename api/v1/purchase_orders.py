// api/v1/purchase_orders.py
"""Purchase Order ingestion and retrieval endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    APIErrorResponse,
    APIListResponse,
    PurchaseOrderCreate,
    PurchaseOrderListItem,
    PurchaseOrderResponse,
    PaginationParams,
)
from core.database import get_db_session
from models import PurchaseOrder, POLine, POStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": APIErrorResponse}},
)
async def ingest_purchase_order(
    payload: PurchaseOrderCreate,
    session: AsyncSession = Depends(get_db_session),
) -> PurchaseOrderResponse:
    """
    Ingest a new purchase order and its line items from the ERP system.

    The PO number must be unique.
    """
    existing = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == payload.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PO number '{payload.po_number}' already exists.",
        )

    po = PurchaseOrder(
        po_number=payload.po_number,
        vendor_number=payload.vendor_number,
        vendor_name=payload.vendor_name,
        po_date=payload.po_date,
        delivery_date=payload.delivery_date,
        total_amount=payload.total_amount,
        currency=payload.currency,
        notes=payload.notes,
        external_reference=payload.external_reference,
        status=POStatus.ACTIVE,
    )
    session.add(po)
    await session.flush()

    for line_payload in payload.lines:
        line = POLine(
            po_id=po.id,
            line_number=line_payload.line_number,
            description=line_payload.description,
            sku=line_payload.sku,
            quantity=line_payload.quantity,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
            tax_rate=line_payload.tax_rate,
        )
        session.add(line)

    await session.commit()
    await session.refresh(po)
    logger.info("PO ingested: id=%s number=%s", po.id, po.po_number)
    return PurchaseOrderResponse.model_validate(po)


@router.get("", response_model=APIListResponse[PurchaseOrderListItem])
async def list_purchase_orders(
    session: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(),
    status_filter: POStatus | None = Query(None, alias="status"),
    vendor_number: str | None = Query(None, max_length=50),
) -> APIListResponse[PurchaseOrderListItem]:
    """Paginated list of purchase orders."""
    stmt = select(PurchaseOrder).where(PurchaseOrder.deleted_at.is_(None))

    if status_filter:
        stmt = stmt.where(PurchaseOrder.status == status_filter)
    if vendor_number:
        stmt = stmt.where(PurchaseOrder.vendor_number == vendor_number)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(PurchaseOrder.created_at.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await session.execute(stmt)
    pos = result.scalars().all()

    items = [PurchaseOrderListItem.model_validate(po) for po in pos]
    pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return APIListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> PurchaseOrderResponse:
    """Retrieve a single purchase order with its line items."""
    result = await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return PurchaseOrderResponse.model_validate(po)
