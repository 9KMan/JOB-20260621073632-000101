# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreateSchema,
    InvoiceListSchema,
    InvoiceResponseSchema,
    InvoiceLineCreateSchema,
    PaginatedResponse,
)
from core.database import DbSession
from models import Invoice, InvoiceLine
from models.enums import InvoiceStatus

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
    description="Create a new invoice with optional line items.",
)
async def create_invoice(
    invoice_data: InvoiceCreateSchema,
    session: DbSession,
) -> Invoice:
    """Create a new invoice."""
    # Check for duplicate invoice number
    existing = await session.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists",
        )

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        vendor_code=invoice_data.vendor_code,
        vendor_name=invoice_data.vendor_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        status=InvoiceStatus.PENDING.value,
        source_system=invoice_data.source_system,
        erp_invoice_id=invoice_data.erp_invoice_id,
        metadata_json=invoice_data.metadata,
    )

    session.add(invoice)
    await session.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            match_status="pending",
        )
        session.add(line)

    await session.commit()
    await session.refresh(invoice)

    return invoice


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceListSchema],
    summary="List invoices",
    description="Retrieve a paginated list of invoices.",
)
async def list_invoices(
    session: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    vendor_code: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    """List invoices with pagination and filters."""
    # Build query
    query = select(Invoice).where(Invoice.deleted_at.is_(None))
    count_query = select(func.count(Invoice.id)).where(Invoice.deleted_at.is_(None))

    if vendor_code:
        query = query.where(Invoice.vendor_code == vendor_code)
        count_query = count_query.where(Invoice.vendor_code == vendor_code)

    if status_filter:
        query = query.where(Invoice.status == status_filter)
        count_query = count_query.where(Invoice.status == status_filter)

    if date_from:
        query = query.where(Invoice.invoice_date >= date_from.date())
        count_query = count_query.where(Invoice.invoice_date >= date_from.date())

    if date_to:
        query = query.where(Invoice.invoice_date <= date_to.date())
        count_query = count_query.where(Invoice.invoice_date <= date_to.date())

    # Get total count
    total = await session.scalar(count_query)
    total = total or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    invoices = result.scalars().all()

    return {
        "items": invoices,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponseSchema,
    summary="Get invoice by ID",
    description="Retrieve a single invoice with line items.",
)
async def get_invoice(
    invoice_id: str,
    session: DbSession,
) -> Invoice:
    """Get invoice by ID."""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return invoice


@router.patch(
    "/{invoice_id}/status",
    response_model=InvoiceResponseSchema,
    summary="Update invoice status",
    description="Update the processing status of an invoice.",
)
async def update_invoice_status(
    invoice_id: str,
    new_status: str,
    session: DbSession,
) -> Invoice:
    """Update invoice status."""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.status = new_status
    await session.commit()
    await session.refresh(invoice)

    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
    description="Soft delete an invoice.",
)
async def delete_invoice(
    invoice_id: str,
    session: DbSession,
) -> None:
    """Soft delete an invoice."""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.soft_delete()
    await session.commit()
