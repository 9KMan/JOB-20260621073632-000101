// api/v1/invoices.py
"""Invoice API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
    SuccessResponse,
)
from core.database import get_db
from models.enums import InvoiceStatus
from models.invoice import Invoice, InvoiceLine

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
    description="Create a new invoice with optional line items.",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Create a new invoice."""
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
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        received_date=invoice_data.received_date,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        paid_amount=invoice_data.paid_amount,
        external_ref=invoice_data.external_ref,
        source_system=invoice_data.source_system,
        description=invoice_data.description,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        status=InvoiceStatus.RECEIVED,
    )
    db.add(invoice)
    await db.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            unit_of_measure=line_data.unit_of_measure,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            po_line_id=line_data.po_line_id,
            delivery_note_line_id=line_data.delivery_note_line_id,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get(
    "/",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="Get a paginated list of invoices with optional filters.",
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_number: str | None = Query(None, description="Filter by vendor"),
    status: InvoiceStatus | None = Query(None, description="Filter by status"),
    invoice_date_from: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    invoice_date_to: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
) -> InvoiceListResponse:
    """Get paginated list of invoices."""
    # Build base query
    query = select(Invoice).where(Invoice.is_deleted == False)
    count_query = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)

    # Apply filters
    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
        count_query = count_query.where(Invoice.vendor_number == vendor_number)
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)
    if invoice_date_from:
        query = query.where(Invoice.invoice_date >= invoice_date_from)
        count_query = count_query.where(Invoice.invoice_date >= invoice_date_from)
    if invoice_date_to:
        query = query.where(Invoice.invoice_date <= invoice_date_to)
        count_query = count_query.where(Invoice.invoice_date <= invoice_date_to)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return InvoiceListResponse(
        items=list(invoices),
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID",
    description="Retrieve a single invoice with its line items.",
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Get an invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
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
    description="Update invoice fields.",
)
async def update_invoice(
    invoice_id: uuid.UUID,
    invoice_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Update an invoice."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.delete(
    "/{invoice_id}",
    response_model=SuccessResponse,
    summary="Delete invoice",
    description="Soft delete an invoice.",
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Soft delete an invoice."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.soft_delete()
    await db.commit()

    return SuccessResponse(message=f"Invoice {invoice_id} deleted successfully")


@router.post(
    "/{invoice_id}/cancel",
    response_model=InvoiceResponse,
    summary="Cancel invoice",
    description="Cancel an invoice.",
)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Cancel an invoice."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.status = InvoiceStatus.CANCELLED
    await db.commit()
    await db.refresh(invoice)
    return invoice
