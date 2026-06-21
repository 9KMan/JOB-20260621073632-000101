// api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    APIListResponse,
    APIErrorResponse,
    InvoiceCreate,
    InvoiceLineResponse,
    InvoiceListItem,
    InvoiceResponse,
    InvoiceUpdateStatus,
    PaginationParams,
)
from core.database import get_db_session
from models import Invoice, InvoiceLine, InvoiceStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": APIErrorResponse}, 409: {"model": APIErrorResponse}},
)
async def ingest_invoice(
    payload: InvoiceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Ingest a new invoice and its line items.

    The invoice number must be unique. Duplicate invoice numbers return 409.
    """
    # Check for duplicate
    existing = await session.execute(
        select(Invoice).where(Invoice.invoice_number == payload.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice number '{payload.invoice_number}' already exists.",
        )

    invoice = Invoice(
        vendor_number=payload.vendor_number,
        vendor_name=payload.vendor_name,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        total_amount=payload.total_amount,
        currency=payload.currency,
        tax_amount=payload.tax_amount,
        notes=payload.notes,
        po_reference_id=payload.po_reference_id,
        external_reference=payload.external_reference,
        status=InvoiceStatus.SUBMITTED,
    )
    session.add(invoice)
    await session.flush()

    # Add line items
    for line_payload in payload.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_payload.line_number,
            description=line_payload.description,
            sku=line_payload.sku,
            quantity=line_payload.quantity,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
            tax_rate=line_payload.tax_rate,
            po_line_id=line_payload.po_line_id,
        )
        session.add(line)

    await session.commit()
    await session.refresh(invoice)
    logger.info("Invoice ingested: id=%s number=%s", invoice.id, invoice.invoice_number)
    return InvoiceResponse.model_validate(invoice)


@router.get("", response_model=APIListResponse[InvoiceListItem])
async def list_invoices(
    session: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(),
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    vendor_number: str | None = Query(None, max_length=50),
    from_date: str | None = Query(None, alias="from_date"),
    to_date: str | None = Query(None, alias="to_date"),
) -> APIListResponse[InvoiceListItem]:
    """
    Paginated list of invoices with optional filtering.
    """
    stmt = select(Invoice).where(Invoice.deleted_at.is_(None))

    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
    if vendor_number:
        stmt = stmt.where(Invoice.vendor_number == vendor_number)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    # Paginate
    stmt = stmt.order_by(Invoice.created_at.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)

    result = await session.execute(stmt)
    invoices = result.scalars().all()

    items = [InvoiceListItem.model_validate(inv) for inv in invoices]
    pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return APIListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """Retrieve a single invoice by ID with its line items."""
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: UUID,
    payload: InvoiceUpdateStatus,
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """Update the status of an existing invoice."""
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    try:
        new_status = InvoiceStatus(payload.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status value: {payload.status}",
        )

    invoice.status = new_status
    if payload.notes:
        invoice.notes = payload.notes
    await session.commit()
    await session.refresh(invoice)
    logger.info("Invoice %s status updated to %s", invoice_id, new_status)
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Soft-delete an invoice."""
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    from datetime import datetime, timezone
    invoice.deleted_at = datetime.now(timezone.utc)
    await session.commit()
