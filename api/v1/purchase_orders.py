# api/v1/purchase_orders.py
"""Purchase Order endpoints for ingestion and retrieval."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models import PurchaseOrder, POLine
from api.schemas import (
    BaseResponse,
    PaginatedResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=BaseResponse[PurchaseOrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new purchase order",
    description="Create a new purchase order from ERP system.",
)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[PurchaseOrderResponse]:
    """Ingest a new purchase order."""
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
    purchase_order = PurchaseOrder(
        po_number=po_data.po_number,
        vendor_id=po_data.vendor_id,
        vendor_name=po_data.vendor_name,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        currency=po_data.currency,
        subtotal=po_data.subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=po_data.total_amount,
        payment_terms=po_data.payment_terms,
        shipping_address=po_data.shipping_address,
        notes=po_data.notes,
        source_system=po_data.source_system,
        metadata_=po_data.metadata,
        status="sent",
    )
    db.add(purchase_order)
    await db.flush()
    
    # Create line items
    for line_data in po_data.lines:
        line = POLine(
            purchase_order_id=purchase_order.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            net_amount=line_data.net_amount,
            tax_amount=line_data.tax_amount,
            tax_rate=line_data.tax_rate,
            promised_date=line_data.promised_date,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(purchase_order)
    
    # Load lines relationship
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == purchase_order.id)
    )
    purchase_order = result.scalar_one()
    
    return BaseResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(purchase_order),
        message="Purchase order created successfully",
    )


@router.get(
    "/",
    response_model=PaginatedResponse[PurchaseOrderResponse],
    summary="List purchase orders",
    description="Get paginated list of purchase orders with optional filters.",
)
async def list_purchase_orders(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    vendor_id: str | None = None,
    status: str | None = None,
    order_date_from: str | None = None,
    order_date_to: str | None = None,
) -> PaginatedResponse[PurchaseOrderResponse]:
    """List purchase orders with pagination and filters."""
    query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
    count_query = select(func.count(PurchaseOrder.id))
    
    # Apply filters
    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
        count_query = count_query.where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)
    
    # Get total count
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    purchase_orders = result.scalars().all()
    
    pages = (total + per_page - 1) // per_page if total else 1
    
    return PaginatedResponse(
        success=True,
        data=[PurchaseOrderResponse.model_validate(po) for po in purchase_orders],
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/{po_id}",
    response_model=BaseResponse[PurchaseOrderResponse],
    summary="Get purchase order by ID",
)
async def get_purchase_order(
    po_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[PurchaseOrderResponse]:
    """Get a single purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    purchase_order = result.scalar_one_or_none()
    
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_id} not found",
        )
    
    return BaseResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(purchase_order),
    )


@router.get(
    "/by-number/{po_number}",
    response_model=BaseResponse[PurchaseOrderResponse],
    summary="Get purchase order by PO number",
)
async def get_purchase_order_by_number(
    po_number: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[PurchaseOrderResponse]:
    """Get a purchase order by its PO number."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.po_number == po_number.upper())
    )
    purchase_order = result.scalar_one_or_none()
    
    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order {po_number} not found",
        )
    
    return BaseResponse(
        success=True,
        data=PurchaseOrderResponse.model_validate(purchase_order),
    )
