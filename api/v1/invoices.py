# api/v1/invoices.py
"""Invoice endpoints for AP Automation Engine."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)
from core.database import get_db_session
from models.enums import InvoiceStatus
from models.invoice import Invoice, InvoiceLine

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
    description="Create a new invoice with line items from ERP or manual entry.",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db_session),
) -> Invoice:
    """Create a new invoice with line items.

    Args:
        invoice_data: The invoice data including line items.
        db: Database session.

    Returns:
        Invoice: The created invoice with lines.

    Raises:
        HTTPException: If invoice creation fails.
    """
    existing = await db.execute(
        select(Invoice).where(
            Invoice.vendor_number == invoice_data.vendor_number,
            Invoice.invoice_number == invoice_data.invoice_number,
            Invoice.is_deleted == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists for vendor {invoice_data.vendor_number}",
        )

    invoice = Invoice(
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        currency_code=invoice_data.currency_code,
        notes=invoice_data.notes,
        source_system=invoice_data.source_system,
        external_reference=invoice_data.external_reference,
        tax_amount=invoice_data.tax_amount,
        is_credit_memo=invoice_data.is_credit_memo,
        status=InvoiceStatus.PENDING,
    )

    db.add(invoice)
    await db.flush()

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
            status=line_data.status,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List all invoices",
    description="Get a paginated list of invoices with optional filtering.",
)
async def list_invoices(
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    vendor_number: str | None = Query(default=None, description="Filter by vendor"),
    status: InvoiceStatus | None = Query(default=None, description="Filter by status"),
    invoice_date_from: date | None = Query(default=None, description="Filter from date"),
    invoice_date_to: date | None = Query(default=None, description="Filter to date"),
    search: str | None = Query(default=None, description="Search in invoice number/vendor name"),
) -> InvoiceListResponse:
    """List invoices with pagination and filtering.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        vendor_number: Optional vendor number filter.
        status: Optional status filter.
        invoice_date_from: Optional start date filter.
        invoice_date_to: Optional end date filter.
        search: Optional search term.

    Returns:
        InvoiceListResponse: Paginated list of invoices.
    """
    query = select(Invoice).where(Invoice.is_deleted == False)
    count_query = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)

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

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Invoice.invoice_number.ilike(search_term))
            | (Invoice.vendor_name.ilike(search_term))
        )
        count_query = count_query.where(
            (Invoice.invoice_number.ilike(search_term))
            | (Invoice.vendor_name.ilike(search_term))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Invoice.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().unique().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

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
    description="Retrieve a single invoice with all line items.",
)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> Invoice:
    """Get a single invoice by ID.

    Args:
        invoice_id: The UUID of the invoice.
        db: Database session.

    Returns:
        Invoice: The invoice with lines.

    Raises:
        HTTPException: If invoice not found.
    """
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
    description="Update an existing invoice's header information.",
)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> Invoice:
    """Update an invoice.

    Args:
        invoice_id: The UUID of the invoice to update.
        invoice_data: The update data.
        db: Database session.

    Returns:
        Invoice: The updated invoice.

    Raises:
        HTTPException: If invoice not found.
    """
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

    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
    description="Soft delete an invoice.",
)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Soft delete an invoice.

    Args:
        invoice_id: The UUID of the invoice to delete.
        db: Database session.

    Raises:
        HTTPException: If invoice not found.
    """
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

    invoice.is_deleted = True
    from datetime import datetime, timezone
    invoice.deleted_at = datetime.now(timezone.utc)

    await db.commit()
