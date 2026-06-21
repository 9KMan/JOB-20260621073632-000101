"""Purchase order ingestion + list/get endpoints."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import POIn, POListResponse, POOut
from core.database import get_session
from models.enums import DocumentStatus
from models.purchase_order import PurchaseOrder, PurchaseOrderLine

router = APIRouter()


@router.post(
    "",
    response_model=POOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a purchase order from ERP",
)
async def create_purchase_order(
    payload: POIn,
    session: AsyncSession = Depends(get_session),
) -> POOut:
    po = PurchaseOrder(
        po_number=payload.po_number,
        vendor_id=payload.vendor_id,
        vendor_name=payload.vendor_name,
        currency=payload.currency.upper(),
        order_date=payload.order_date,
        expected_delivery=payload.expected_delivery,
        total_amount=payload.total_amount,
        buyer=payload.buyer,
        notes=payload.notes,
        status=DocumentStatus.INGESTED,
    )
    for line in payload.lines:
        po.lines.append(_line_from_payload(line))  # type: ignore[arg-type]
    session.add(po)
    await session.flush()
    await session.refresh(po, attribute_names=["lines"])
    return POOut.model_validate(po)


@router.get(
    "",
    response_model=POListResponse,
    summary="List purchase orders",
)
async def list_purchase_orders(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    vendor_id: Optional[uuid.UUID] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> POListResponse:
    stmt = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    count_stmt = select(func.count()).select_from(PurchaseOrder)
    if vendor_id is not None:
        stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
        count_stmt = count_stmt.where(PurchaseOrder.vendor_id == vendor_id)

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    items = [POOut.model_validate(row) for row in result.scalars().all()]
    return POListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{po_id}",
    response_model=POOut,
    summary="Get purchase order by id",
)
async def get_purchase_order(
    po_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> POOut:
    po = await session.get(PurchaseOrder, po_id)
    if po is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return POOut.model_validate(po)


def _line_from_payload(line):  # type: ignore[no-untyped-def]
    return PurchaseOrderLine(
        line_number=line.line_number,
        sku=line.sku,
        description=line.description,
        ordered_qty=line.ordered_qty,
        unit_price=line.unit_price,
        line_total=line.line_total,
        uom=line.uom,
        gl_account=line.gl_account,
        cost_center=line.cost_center,
    )
