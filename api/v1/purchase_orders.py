# api/v1/purchase_orders.py
"""Purchase Order endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
)
from core.database import get_db
from models import POStatus, POLine, PurchaseOrder

router = APIRouter()

PODB = Annotated[AsyncSession, get_db]


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
    db: PODB,
) -> PurchaseOrderResponse:
    """Create a new purchase order with line items."""
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_data.po_number,
            PurchaseOrder.is_deleted == False,  # noqa: E712
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase Order {po_data.po_number} already exists",
        )

    # Create PO header
    po = PurchaseOrder(
        po_number=po_data.po_number,
        vendor_id=po_data.vendor_id,
        vendor_name=po_data.vendor_name,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        gross_amount=po_data.gross_amount,
        tax_amount=po_data.tax_amount,
        net_amount=po_data.net_amount,
        currency=po_data.currency,
        status=POStatus.OPEN.value,
        payment_terms=po_data.payment_terms,
        ship_to=po_data.ship_to,
        notes=po_data.notes,
        is_blanket=po_data.is_blanket,
        blanket_po_id=po_data.blanket_po_id,
        source_system=po_data.source_system,
        external_ref=po_data.external_ref,
    )

    db.add(po)
    await db.flush()

    # Create line items
    for line_data in po_data.lines:
        line = POLine(
            po_id=po.id,
            line_number=line_data.line_number,
            description=line_data.description,
            part_number=line_data.part_number,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            gross_amount=line_data.gross_amount,
            tax_amount=line_data.tax_amount,
            net_amount=line_data.net_amount,
            schedule_date=line_data.schedule_date,
            promised_date=line_data.promised_date,
        )
        db.add(line)

    await db.commit()
    await db.refresh(po)

    return PurchaseOrderResponse.model_validate(po)


@router.get(
    "",
    response_model=PaginatedResponse[PurchaseOrderResponse],
)
async def list_purchase_orders(
    db: PODB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = None,
    status: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> PaginatedResponse[PurchaseOrderResponse]:
    """List purchase orders with pagination and filters."""
    query = select(PurchaseOrder).where(
        PurchaseOrder.is_deleted == False  # noqa: E712
    )

    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        query = query.where(PurchaseOrder.status == status)

    # Count total
    from sqlalchemy import func

    count_query = select(func.count(PurchaseOrder.id)).where(
        PurchaseOrder.is_deleted == False  # noqa: E712
    )
    if vendor_id:
        count_query = count_query.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        count_query = count_query.where(PurchaseOrder.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(PurchaseOrder.created_at.desc())

    result = await db.execute(query)
    pos = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        data=[PurchaseOrderResponse.model_validate(po) for po in pos],
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_purchase_order(
    po_id: UUID,
    db: PODB,
) -> PurchaseOrderResponse:
    """Get purchase order by ID with line items."""
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.is_deleted == False,  # noqa: E712
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    return PurchaseOrderResponse.model_validate(po)
