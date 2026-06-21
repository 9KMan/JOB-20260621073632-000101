# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    PaginatedResponse,
    ErrorResponse,
)
from core.database import get_db
from models import Invoice, InvoiceLine, InvoiceStatus

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Create a new invoice with line items."""
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number {invoice_data.invoice_number} already exists",
        )

    invoice = Invoice(
        id=str(uuid4()),
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        invoice_amount=invoice_data.invoice_amount,
        tax_amount=invoice_data.tax_amount,
        currency=invoice_data.currency,
        po_reference=invoice_data.po_reference,
        notes=invoice_data.notes,
        status=InvoiceStatus.DRAFT.value,
    )

    for line_data in invoice_data.lines:
        line = InvoiceLine(
            id=str(uuid4()),
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_code=line_data.tax_code,
            notes=line_data.notes,
            po_line_reference=line_data.po_line_reference,
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
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status: str | None = Query(None, description="Filter by status"),
    invoice_date_from: datetime | None = Query(None, description="Filter from date"),
    invoice_date_to: datetime | None = Query(None, description="Filter to date"),
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with pagination and filtering."""
    query = select(Invoice).where(Invoice.is_active == True)

    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
    if status:
        query = query.where(Invoice.status == status)
    if invoice_date_from:
        query = query.where(Invoice.invoice_date >= invoice_date_from)
    if invoice_date_to:
        query = query.where(Invoice.invoice_date <= invoice_date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Invoice.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Get a specific invoice by ID."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Update an existing invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )

    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    invoice.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def delete_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )

    invoice.is_active = False
    invoice.updated_at = datetime.now(timezone.utc)
    await db.flush()
