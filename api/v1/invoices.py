# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.database import get_db
from core.config import settings
from models import Invoice, InvoiceLine
from models.enums import InvoiceStatus, LineStatus
from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceLineResponse,
    ErrorResponse,
    PaginationParams,
)

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Invoice already exists"},
    },
    summary="Ingest a new invoice",
    description="Create a new invoice with its line items. Fails if invoice_number already exists.",
)
async def ingest_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Ingest a new invoice from the ERP / OCR system."""
    # Build the invoice object
    invoice = Invoice(
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        vendor_name=payload.vendor_name,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        currency=payload.currency,
        status=InvoiceStatus.RECEIVED,
        notes=payload.notes,
    )

    for line_data in payload.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            status=LineStatus.OPEN,
        )
        invoice.lines.append(line)

    try:
        db.add(invoice)
        await db.flush()
        await db.refresh(invoice, attribute_names=["lines"])
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number '{payload.invoice_number}' already exists.",
        )

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="Returns a paginated list of invoices with optional status filter.",
)
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    vendor_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> InvoiceListResponse:
    """Return a paginated list of invoices."""
    # Base query
    base_q = select(Invoice).where(Invoice.is_deleted == False)  # noqa: E712

    if status_filter:
        base_q = base_q.where(Invoice.status == status_filter)
    if vendor_id:
        base_q = base_q.where(Invoice.vendor_id == vendor_id)

    # Count total
    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginated fetch
    q = (
        base_q
        .order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(q)
    invoices = result.scalars().unique().all()

    items = [InvoiceResponse.model_validate(inv) for inv in invoices]
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return InvoiceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID",
    responses={
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Return a single invoice with its line items."""
    q = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(q)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found.",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/{invoice_id}/status",
    response_model=InvoiceResponse,
    summary="Update invoice status",
    responses={
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def update_invoice_status(
    invoice_id: uuid.UUID,
    new_status: str = Query(..., description="New status value"),
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Update the status of an invoice."""
    q = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(q)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found.",
        )

    # Validate the status is a known enum value
    try:
        InvoiceStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'.",
        )

    invoice.status = InvoiceStatus(new_status)
    invoice.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an invoice",
    responses={
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete an invoice and all its line items."""
    q = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(q)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found.",
        )

    invoice.is_deleted = True
    invoice.deleted_at = datetime.now(timezone.utc)
    await db.flush()
