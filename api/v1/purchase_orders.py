# api/v1/purchase_orders.py
"""Purchase order ingestion and list/get endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PaginatedResponse,
    PageParams,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
)
from core.database import get_db
from core.security import get_current_user_id
from models import BalanceLedger, BalanceLedgerLine, PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus

router = APIRouter()


@router.post(
    "/",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new purchase order",
)
async def ingest_purchase_order(
    payload: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> PurchaseOrderResponse:
    """Ingest a new purchase order with its line items and seed balance ledger."""
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder.id).where(PurchaseOrder.po_number == payload.po_number)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PO number '{payload.po_number}' already exists",
        )

    po = PurchaseOrder(
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        po_number=payload.po_number,
        po_date=payload.po_date,
        delivery_date=payload.delivery_date,
        currency=payload.currency,
        total_amount=payload.total_amount,
        status=PurchaseOrderStatus.ACTIVE,
        erp_po_id=payload.erp_po_id,
    )
    db.add(po)
    await db.flush()

    for line_payload in payload.lines:
        line = PurchaseOrderLine(
            po_id=po.id,
            line_number=line_payload.line_number,
            description=line_payload.description,
            product_code=line_payload.product_code,
            product_name=line_payload.product_name,
            quantity_ordered=line_payload.quantity_ordered,
            unit_of_measure=line_payload.unit_of_measure,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
        )
        db.add(line)

    # Seed balance ledger at PO level and per line
    ledger = BalanceLedger(
        po_id=po.id,
        currency=payload.currency,
        total_open_amount=payload.total_amount,
    )
    db.add(ledger)
    await db.flush()

    for line in payload.lines:
        ledger_line = BalanceLedgerLine(
            ledger_id=ledger.id,
            po_line_id=line.id,  # resolved after flush
            qty_ordered=line.quantity_ordered,
            qty_pending=line.quantity_ordered,
            amount_ordered=line.line_amount,
            amount_pending=line.line_amount,
        )
        db.add(ledger_line)

    await db.commit()
    await db.refresh(po)
    return PurchaseOrderResponse.model_validate(po)


@router.get("/", response_model=PaginatedResponse)
async def list_purchase_orders(
    params: PageParams = Depends(),
    status_filter: PurchaseOrderStatus | None = Query(None, alias="status"),
    vendor_code: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> PaginatedResponse:
    """List all purchase orders with optional filtering and pagination."""
    stmt = select(PurchaseOrder)
    count_stmt = select(func.count(PurchaseOrder.id))

    if status_filter:
        stmt = stmt.where(PurchaseOrder.status == status_filter)
        count_stmt = count_stmt.where(PurchaseOrder.status == status_filter)
    if vendor_code:
        stmt = stmt.where(PurchaseOrder.vendor_code == vendor_code)
        count_stmt = count_stmt.where(PurchaseOrder.vendor_code == vendor_code)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(PurchaseOrder.created_at.desc()).offset(params.offset).limit(params.page_size)
    rows = (await db.execute(stmt)).scalars().all()

    items = [PurchaseOrderListResponse.model_validate(r) for r in rows]
    return PaginatedResponse.create(items, total, params)


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> PurchaseOrderResponse:
    """Retrieve a single purchase order with its line items."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )
    return PurchaseOrderResponse.model_validate(po)
