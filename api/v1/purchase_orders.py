# api/v1/purchase_orders.py
"""Purchase Order endpoints for AP Automation Engine."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
)
from core.database import get_db_session
from models.enums import PurchaseOrderStatus
from models.purchase_order import PurchaseOrder, POLine

router = APIRouter()


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new purchase order",
    description="Create a new purchase order with line items from ERP.",
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db_session),
) -> PurchaseOrder:
    """Create a new purchase order with line items.

    Args:
        po_data: The PO data including line items.
        db: Database session.

    Returns:
        PurchaseOrder: The created PO with lines.

    Raises:
        HTTPException: If PO creation fails.
    """
    existing = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_data.po_number,
            PurchaseOrder.is_deleted == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order {po_data.po_number} already exists",
        )

    purchase_order = PurchaseOrder(
        vendor_number=po_data.vendor_number,
        vendor_name=po_data.vendor_name,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        total_amount=po_data.total_amount,
        currency_code=po_data.currency_code,
        notes=po_data.notes,
        source_system=po_data.source_system,
        department_code=po_data.department_code,
        cost_center=po_data.cost_center,
        status=PurchaseOrderStatus.OPEN,
    )

    db.add(purchase_order)
    await db.flush()

    for line_data in po_data.lines:
        line = POLine(
            po_id=purchase_order.id,
            line_number=line_data.line_number,
            item_number=line_data.item_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            status=line_data.status,
            delivery_date=line_data.delivery_date,
        )
        db.add(line)

    await db.commit()
    await db.refresh(purchase_order)

    return purchase_order


@router.get(
    "",
    response_model=PurchaseOrderListResponse,
    summary="List all purchase orders",
    description="Get a paginated list of purchase orders with optional filtering.",
)
async def list_purchase_orders(
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    vendor_number: str | None = Query(default=None, description="Filter by vendor"),
    status: PurchaseOrderStatus | None = Query(default=None, description="Filter by status"),
    po_date_from: date | None = Query(default=None, description="Filter from date"),
    po_date_to: date | None = Query(default=None, description="Filter to date"),
    search: str | None = Query(default=None, description="Search in PO number/vendor name"),
) -> PurchaseOrderListResponse:
    """List purchase orders with pagination and filtering.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        vendor_number: Optional vendor number filter.
        status: Optional status filter.
        po_date_from: Optional start date filter.
        po_date_to: Optional end date filter.
        search: Optional search term.

    Returns:
        PurchaseOrderListResponse: Paginated list of purchase orders.
    """
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
    count_query = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.is_deleted == False)

    if vendor_number:
        query = query.where(PurchaseOrder.vendor_number == vendor_number)
        count_query = count_query.where(PurchaseOrder.vendor_number == vendor_number)

    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)

    if po_date_from:
        query = query.where(PurchaseOrder.po_date >= po_date_from)
        count_query = count_query.where(PurchaseOrder.po_date >= po_date_from)

    if po_date_to:
        query = query.where(PurchaseOrder.po_date <= po_date_to)
        count_query = count_query.where(PurchaseOrder.po_date <= po_date_to)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (PurchaseOrder.po_number.ilike(search_term))
            | (PurchaseOrder.vendor_name.ilike(search_term))
        )
        count_query = count_query.where(
            (PurchaseOrder.po_number.ilike(search_term))
            | (PurchaseOrder.vendor_name.ilike(search_term))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(PurchaseOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    purchase_orders = result.scalars().unique().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PurchaseOrderListResponse(
        items=list(purchase_orders),
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Get purchase order by ID",
    description="Retrieve a single purchase order with all line items.",
)
async def get_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> PurchaseOrder:
    """Get a single purchase order by ID.

    Args:
        po_id: The UUID of the purchase order.
        db: Database session.

    Returns:
        PurchaseOrder: The purchase order with lines.

    Raises:
        HTTPException: If purchase order not found.
    """
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
    description="Retrieve a purchase order by its PO number.",
)
async def get_purchase_order_by_number(
    po_number: str,
    db: AsyncSession = Depends(get_db_session),
) -> PurchaseOrder:
    """Get a purchase order by its PO number.

    Args:
        po_number: The PO number.
        db: Database session.

    Returns:
        PurchaseOrder: The purchase order with lines.

    Raises:
        HTTPException: If purchase order not found.
    """
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
