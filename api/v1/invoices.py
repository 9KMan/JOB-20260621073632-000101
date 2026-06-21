# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    ErrorResponse,
    InvoiceCreate,
    InvoiceLineResponse,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationParams,
)
from core.database import get_db
from models import Invoice, InvoiceLine, DocumentStatus

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Invoice already exists"},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Ingest a new invoice with its lines."""
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number {invoice_data.invoice_number} already exists",
        )

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        vendor_address=invoice_data.vendor_address,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        received_date=datetime.now(timezone.utc),
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        paid_amount=invoice_data.paid_amount,
        notes=invoice_data.notes,
        internal_reference=invoice_data.internal_reference,
        status=DocumentStatus.PENDING,
    )

    # Create invoice lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            description=line_data.description,
            item_number=line_data.item_number,
            sku=line_data.sku,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
        )
        invoice.lines.append(line)

    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/",
    response_model=PaginatedResponse[InvoiceResponse],
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    vendor_number: Annotated[str | None, Query(description="Filter by vendor number")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    date_from: Annotated[datetime | None, Query(description="Filter by invoice date from")] = None,
    date_to: Annotated[datetime | None, Query(description="Filter by invoice date to")] = None,
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with optional filters."""
    query = select(Invoice).options(selectinload(Invoice.lines))

    # Apply filters
    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
    if status:
        query = query.where(Invoice.status == status)
    if date_from:
        query = query.where(Invoice.invoice_date >= date_from.date())
    if date_to:
        query = query.where(Invoice.invoice_date <= date_to.date())

    # Count total
    count_query = select(func.count()).select_from(Invoice)
    if vendor_number:
        count_query = count_query.where(Invoice.vendor_number == vendor_number)
    if status:
        count_query = count_query.where(Invoice.status == status)
    if date_from:
        count_query = count_query.where(Invoice.invoice_date >= date_from.date())
    if date_to:
        count_query = count_query.where(Invoice.invoice_date <= date_to.date())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(pagination.offset).limit(pagination.limit)
    query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    items = [InvoiceResponse.model_validate(inv) for inv in invoices]
    return PaginatedResponse.create(items, total, pagination.page, pagination.page_size)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Get a specific invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
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
    responses={
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Update an existing invoice."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields if provided
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "status" and value:
            setattr(invoice, field, DocumentStatus(value))
        else:
            setattr(invoice, field, value)

    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an invoice (soft delete)."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.is_deleted = True
    invoice.deleted_at = datetime.now(timezone.utc)
    await db.flush()
