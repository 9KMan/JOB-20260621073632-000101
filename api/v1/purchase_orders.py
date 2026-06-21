# api/v1/purchase_orders.py
"""Purchase Order endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    ApiResponse,
    ErrorResponse,
    PaginatedResponse,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
)
from core.database import get_db
from models.enums import PurchaseOrderStatus
from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from services.anchoring import AnchoringService

router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[PurchaseOrderResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PurchaseOrderResponse]:
    """
    Ingest a new purchase order from ERP.

    Creates a PO with line items. The PO becomes available for matching.
    """
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase Order {po_data.po_number} already exists",
        )

    # Create PO
    po = PurchaseOrder(
        vendor_number=po_data.vendor_number,
        vendor_name=po_data.vendor_name,
        po_number=po_data.po_number,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        subtotal=po_data.subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        payment_terms=po_data.payment_terms,
        shipping_terms=po_data.shipping_terms,
        description=po_data.description,
        erp_id=po_data.erp_id,
        raw_data=po_data.raw_data,
        status=PurchaseOrderStatus.ACTIVE,
    )

    # Create line items
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            line_number=line_data.line_number,
            item_number=line_data.item_number,
            description=line_data.description,
            ordered_quantity=line_data.ordered_quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            remaining_quantity=line_data.ordered_quantity,
            remaining_amount=line_data.line_amount,
        )
        po.lines.append(line)

    db.add(po)
    await db.flush()

    # Load the lines relationship
    await db.refresh(po, ["lines"])

    return ApiResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(po),
        message="Purchase Order created successfully",
    )


@router.get(
    "/",
    response_model=PaginatedResponse[PurchaseOrderListResponse],
)
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor_number: str | None = None,
    status: PurchaseOrderStatus | None = None,
    po_number: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PurchaseOrderListResponse]:
    """
    List all purchase orders with pagination and filtering.
    """
    query = select(PurchaseOrder).where(PurchaseOrder.deleted_at.is_(None))

    # Apply filters
    if vendor_number:
        query = query.where(PurchaseOrder.vendor_number == vendor_number)
    if status:
        query = query.where(PurchaseOrder.status == status)
    if po_number:
        query = query.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))

    # Count total
    count_query = select(PurchaseOrder.id).where(PurchaseOrder.deleted_at.is_(None))
    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # Apply pagination
    query = query.order_by(PurchaseOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    purchase_orders = result.scalars().all()

    items = [PurchaseOrderListResponse.model_validate(po) for po in purchase_orders]
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{po_id}",
    response_model=ApiResponse[PurchaseOrderResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PurchaseOrderResponse]:
    """
    Get a single purchase order by ID with all line items.
    """
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id, PurchaseOrder.deleted_at.is_(None))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    return ApiResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(po),
    )


@router.get(
    "/number/{po_number}",
    response_model=ApiResponse[PurchaseOrderResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_purchase_order_by_number(
    po_number: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PurchaseOrderResponse]:
    """
    Get a purchase order by its PO number.
    """
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.po_number == po_number, PurchaseOrder.deleted_at.is_(None))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_number} not found",
        )

    return ApiResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(po),
    )


@router.patch(
    "/{po_id}/close",
    response_model=ApiResponse[PurchaseOrderResponse],
    responses={404: {"model": ErrorResponse}},
)
async def close_purchase_order(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PurchaseOrderResponse]:
    """
    Close a purchase order and all its lines.
    """
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id, PurchaseOrder.deleted_at.is_(None))
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    if po.status == PurchaseOrderStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase Order is already closed",
        )

    po.status = PurchaseOrderStatus.CLOSED
    for line in po.lines:
        line.is_closed = True

    await db.flush()
    await db.refresh(po, ["lines"])

    return ApiResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(po),
        message="Purchase Order closed successfully",
    )
