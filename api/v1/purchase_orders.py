// api/v1/purchase_orders.py
"""Purchase order ingestion and CRUD endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PaginatedResponse,
    PaginationParams,
    ErrorResponse,
)
from core.database import get_db_session
from models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus

router = APIRouter()


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
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderResponse:
    """
    Ingest a new purchase order from ERP.

    Creates a PO header and its associated line items.
    """
    # Check for duplicate PO
    existing = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_data.po_number,
            PurchaseOrder.is_deleted == False,
        )
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
        vendor_tax_id=po_data.vendor_tax_id,
        po_number=po_data.po_number,
        po_date=po_data.po_date,
        delivery_date=po_data.delivery_date,
        po_amount=po_data.po_amount,
        currency_code=po_data.currency_code,
        description=po_data.description,
        payment_terms=po_data.payment_terms,
        shipping_terms=po_data.shipping_terms,
        requested_by=po_data.requested_by,
        status=PurchaseOrderStatus.SUBMITTED,
    )

    db.add(po)
    await db.flush()

    # Create line items
    for line_data in po_data.lines:
        line = PurchaseOrderLine(
            po_id=po.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    pagination: Annotated[PaginationParams, Query()],
    vendor_number: Annotated[str | None, Query(description="Filter by vendor")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    po_date_from: Annotated[str | None, Query(description="Filter from date (YYYY-MM-DD)")] = None,
    po_date_to: Annotated[str | None, Query(description="Filter to date (YYYY-MM-DD)")] = None,
) -> PaginatedResponse[PurchaseOrderResponse]:
    """
    List all purchase orders with pagination and filtering.
    """
    query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
    count_query = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.is_deleted == False)

    if vendor_number:
        query = query.where(PurchaseOrder.vendor_number == vendor_number)
        count_query = count_query.where(PurchaseOrder.vendor_number == vendor_number)

    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)

    total = (await db.execute(count_query)).scalar_one()

    query = query.offset(pagination.offset).limit(pagination.limit)
    query = query.order_by(PurchaseOrder.created_at.desc())

    result = await db.execute(query)
    pos = result.scalars().all()

    items = [PurchaseOrderResponse.model_validate(po) for po in pos]
    return PaginatedResponse.create(items, total, pagination)


@router.get(
    "/{po_id}",
    response_model=PurchaseOrderResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_purchase_order(
    po_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderResponse:
    """
    Get a single purchase order by ID.
    """
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == uuid.UUID(po_id),
            PurchaseOrder.is_deleted == False,
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    return PurchaseOrderResponse.model_validate(po)


@router.get(
    "/{po_id}/balance",
    response_model=dict,
)
async def get_po_balance(
    po_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """
    Get the remaining balance for a purchase order.
    """
    from models import BalanceLedger, LedgerEntryType

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == uuid.UUID(po_id),
            PurchaseOrder.is_deleted == False,
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {po_id} not found",
        )

    # Get latest balance from ledger
    latest_balance = await db.execute(
        select(BalanceLedger)
        .where(
            BalanceLedger.po_id == uuid.UUID(po_id),
            BalanceLedger.entry_type == LedgerEntryType.PO_INITIAL,
        )
        .order_by(BalanceLedger.created_at.desc())
        .limit(1)
    )

    balance = latest_balance.scalar_one_or_none()

    if balance:
        return {
            "po_id": str(po_id),
            "po_amount": float(po.po_amount),
            "quantity_balance": float(balance.quantity_balance_after),
            "amount_balance": float(balance.amount_balance_after),
            "currency_code": po.currency_code,
        }
    else:
        # No ledger entries yet, return full PO amount
        return {
            "po_id": str(po_id),
            "po_amount": float(po.po_amount),
            "quantity_balance": float(sum(line.quantity for line in po.lines)),
            "amount_balance": float(po.po_amount),
            "currency_code": po.currency_code,
        }
