# api/v1/invoices.py
"""Invoice endpoints for AP Automation Engine.

Handles invoice ingestion, CRUD operations, and retrieval.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
)
from core.database import get_db
from core.security import get_current_user_id
from models.enums import InvoiceStatus
from models.invoice import Invoice, InvoiceLine

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
    description="Create a new invoice with line items from vendor/ERP data.",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> Invoice:
    """Create a new invoice.

    Args:
        invoice_data: Invoice data including line items
        db: Database session
        user_id: Current user ID

    Returns:
        Invoice: Created invoice with lines
    """
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        status=InvoiceStatus.PENDING_REVIEW.value,
    )

    db.add(invoice)
    await db.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            line_total=line_data.line_total,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice, ["lines"])

    return invoice


@router.get(
    "/",
    response_model=PaginatedResponse[InvoiceListResponse],
    summary="List invoices",
    description="Retrieve a paginated list of invoices with optional filters.",
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    vendor_id: str | None = Query(default=None, description="Filter by vendor"),
    status_filter: InvoiceStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by status",
    ),
    date_from: datetime | None = Query(
        default=None,
        description="Filter from date",
    ),
    date_to: datetime | None = Query(
        default=None,
        description="Filter to date",
    ),
) -> PaginatedResponse[InvoiceListResponse]:
    """List invoices with pagination and filters.

    Args:
        db: Database session
        page: Page number
        page_size: Items per page
        vendor_id: Optional vendor filter
        status_filter: Optional status filter
        date_from: Optional start date filter
        date_to: Optional end date filter

    Returns:
        PaginatedResponse: Paginated invoice list
    """
    # Build query
    query = select(Invoice).where(Invoice.is_deleted == False)

    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)

    if status_filter:
        query = query.where(Invoice.status == status_filter.value)

    if date_from:
        query = query.where(Invoice.invoice_date >= date_from.date())

    if date_to:
        query = query.where(Invoice.invoice_date <= date_to.date())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Invoice.invoice_date.desc(), Invoice.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    # Convert to response format
    items = [
        InvoiceListResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            vendor_id=inv.vendor_id,
            vendor_name=inv.vendor_name,
            invoice_date=inv.invoice_date,
            total_amount=inv.total_amount,
            currency=inv.currency,
            status=inv.status,
            match_score=inv.match_score,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]

    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID",
    description="Retrieve a single invoice with line items.",
)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Get invoice by ID.

    Args:
        invoice_id: Invoice UUID
        db: Database session

    Returns:
        Invoice: Invoice with lines

    Raises:
        HTTPException: If invoice not found
    """
    query = (
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
        .where(Invoice.is_deleted == False)
    )

    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return invoice


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update invoice",
    description="Update invoice fields (status, notes, etc.).",
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> Invoice:
    """Update invoice.

    Args:
        invoice_id: Invoice UUID
        update_data: Fields to update
        db: Database session
        user_id: Current user ID

    Returns:
        Invoice: Updated invoice

    Raises:
        HTTPException: If invoice not found
    """
    query = (
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
        .where(Invoice.is_deleted == False)
    )

    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    if "status" in update_dict:
        update_dict["status"] = update_data.status.value

    for key, value in update_dict.items():
        setattr(invoice, key, value)

    await db.commit()
    await db.refresh(invoice, ["lines"])

    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
    description="Soft delete an invoice.",
)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> None:
    """Soft delete invoice.

    Args:
        invoice_id: Invoice UUID
        db: Database session
        user_id: Current user ID

    Raises:
        HTTPException: If invoice not found
    """
    query = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )

    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.is_deleted = True
    invoice.deleted_at = datetime.now(timezone.utc)

    await db.commit()
