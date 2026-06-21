# api/v1/purchase_orders.py
"""Purchase order endpoints for ingestion and retrieval."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PaginatedResponse,
    PaginationMeta,
    BalanceSummaryResponse,
)
from core.database import get_db
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.balance_ledger import BalanceSummary
from models.enums import PurchaseOrderStatus

router = APIRouter()


@router.post(
    "/",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create purchase order",
    description="Ingest a new purchase order from ERP.",
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrder:
    """
    Create a new purchase order with line items.
    """
    # Check for duplicate PO number
    stmt = select(PurchaseOrder).where(
        PurchaseOrder.po_number == po_data.po_number,
        PurchaseOrder.is_deleted == False,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order {po_data.po_number} already exists",
        )

    # Create PO
    purchase_order = PurchaseOrder(
        vendor_id=po_data.vendor_id,
        vendor_name=po_data.vendor_name,
        vendor_code=po_data.vendor_code,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        expected_delivery_date=po_data.expected_delivery_date,
        subtotal=po_data.subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        source_system=po_data.source_system,
        terms=po_data.terms,
        notes=po_data.notes,
        status=PurchaseOrderStatus.ACTIVE,
    )

    db.add(purchase_order)
    await db.flush()

    # Create PO lines
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            po_id=purchase_order.id,
            line_number=line_data.line_number,
            description=line_data.description,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            quantity_ordered=line_data.quantity_ordered,
            unit_price=line_data.unit_price,
            extended_amount=line_data.extended_amount,
            tax_rate=line_data.tax_rate or 0,
            tax_amount=line_data.tax_amount or 0,
        )
        db.add(line)

    await db.commit()
    await db.refresh(purchase_order)

    return purchase_order


@router.get(
    "/",
    response_model=PaginatedResponse[PurchaseOrderListResponse],
    summary="List purchase orders",
    description="Get a paginated list of purchase orders.",
)
async def list_purchase_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_id: Optional[uuid.UUID] = Query(None, description="Filter by vendor"),
    status: Optional[PurchaseOrderStatus] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter from date"),
    end_date: Optional[str] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List purchase orders with pagination and optional filters.
    """
    stmt = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)

    if vendor_id:
        stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    if start_date:
        stmt = stmt.where(PurchaseOrder.po_date >= start_date)
    if end_date:
        stmt = stmt.where(PurchaseOrder.po_date <= end_date)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * per_page
    stmt = stmt.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(stmt)
    purchase_orders = result.scalars().all()

    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "data": purchase_orders,
        "meta": PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        ),
    }


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Get purchase order",
    description="Get a single purchase order by ID.",
)
async def get_purchase_order(
    po_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrder:
    """
    Get purchase order by ID with line items.
    """
    stmt = select(PurchaseOrder).where(
        PurchaseOrder.id == po_id,
        PurchaseOrder.is_deleted == False,
    )
    result = await db.execute(stmt)
    purchase_order = result.scalar_one_or_none()

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    return purchase_order


@router.get(
    "/{po_id}/lines/{line_id}/balance",
    response_model=BalanceSummaryResponse,
    summary="Get PO line balance",
    description="Get the balance summary for a PO line.",
)
async def get_po_line_balance(
    po_id: uuid.UUID,
    line_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BalanceSummary:
    """
    Get balance summary for a specific PO line.
    """
    # Verify PO exists
    po_stmt = select(PurchaseOrder).where(
        PurchaseOrder.id == po_id,
        PurchaseOrder.is_deleted == False,
    )
    po_result = await db.execute(po_stmt)
    if not po_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )

    # Get balance summary
    stmt = select(BalanceSummary).where(BalanceSummary.po_line_id == line_id)
    result = await db.execute(stmt)
    balance = result.scalar_one_or_none()

    if not balance:
        # Return default balance if not found
        line_stmt = select(PurchaseOrderLine).where(PurchaseOrderLine.id == line_id)
        line_result = await db.execute(line_stmt)
        line = line_result.scalar_one_or_none()

        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PO line {line_id} not found",
            )

        return BalanceSummary(
            po_line_id=line_id,
            quantity_ordered=line.quantity_ordered,
            quantity_delivered=line.quantity_received,
            quantity_invoiced=line.quantity_invoiced,
            quantity_credited=0,
            quantity_balance=line.quantity_ordered - line.quantity_invoiced,
            amount_ordered=line.extended_amount,
            amount_delivered=0,
            amount_invoiced=0,
            amount_credited=0,
            amount_balance=line.extended_amount,
            delivery_percentage=0,
            invoice_percentage=0,
        )

    return balance
