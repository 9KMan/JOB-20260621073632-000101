# api/v1/invoices.py
"""Invoice API endpoints.

Provides CRUD operations and ingestion for AP invoices.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceListItem,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    ErrorResponse,
)
from core.database import get_db_session
from models.enums import InvoiceStatus
from models.invoice import Invoice, InvoiceLine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """Create a new invoice with line items.

    Ingests a new invoice from an external source (ERP, OCR, etc.)
    and stores it in the database.
    """
    # Check for duplicate invoice
    existing = await db.execute(
        select(Invoice).where(
            Invoice.invoice_number == invoice_data.invoice_number,
            Invoice.supplier_id == invoice_data.supplier_id,
            Invoice.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists for supplier {invoice_data.supplier_id}",
        )

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency=invoice_data.currency,
        po_reference=invoice_data.po_reference,
        notes=invoice_data.notes,
        status=InvoiceStatus.PENDING,
        received_at=datetime.utcnow(),
    )

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            sku=line_data.sku,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            tax_rate=line_data.tax_rate,
        )
        invoice.lines.append(line)

    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    logger.info(f"Created invoice {invoice.id}: {invoice.invoice_number}")

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceListItem],
)
async def list_invoices(
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: str | None = Query(None),
    status: InvoiceStatus | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    search: str | None = Query(None),
) -> PaginatedResponse[InvoiceListItem]:
    """List invoices with pagination and filtering.

    Supports filtering by supplier, status, date range, and search.
    """
    query = select(Invoice).where(Invoice.deleted_at.is_(None))

    # Apply filters
    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
    if status:
        query = query.where(Invoice.status == status)
    if date_from:
        query = query.where(Invoice.invoice_date >= date_from.date())
    if date_to:
        query = query.where(Invoice.invoice_date <= date_to.date())
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            Invoice.invoice_number.ilike(search_pattern)
            | Invoice.supplier_name.ilike(search_pattern)
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Apply pagination
    query = query.order_by(Invoice.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    items = [InvoiceListItem.model_validate(inv) for inv in invoices]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """Get a single invoice by ID with all line items."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_invoice(
    invoice_id: str,
    update_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """Update an invoice's metadata or status.

    Only allows updates to unlocked invoices.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    if invoice.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update locked invoice",
        )

    # Apply updates
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(invoice, field, value)

    await db.flush()
    await db.refresh(invoice)

    logger.info(f"Updated invoice {invoice_id}")

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Soft delete an invoice.

    Invoices that are locked or have been matched cannot be deleted.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    if invoice.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete locked invoice",
        )

    # Soft delete
    invoice.deleted_at = datetime.utcnow()
    await db.flush()

    logger.info(f"Deleted invoice {invoice_id}")
