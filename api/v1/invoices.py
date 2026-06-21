# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    SuccessResponse,
)
from core.database import get_db
from models import Invoice, InvoiceLine
from models.enums import InvoiceStatus

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
)
async def ingest_invoice(
    payload: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Ingest a new invoice with line items.

    The invoice is validated, persisted, and returned with assigned IDs.
    Matching is triggered separately via POST /matching/trigger.
    """
    # Check for duplicate
    existing = await db.execute(
        select(Invoice).where(
            Invoice.vendor_code == payload.vendor_code,
            Invoice.invoice_number == payload.invoice_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {payload.invoice_number} already exists for vendor {payload.vendor_code}",
        )

    # Build invoice
    invoice = Invoice(
        invoice_number=payload.invoice_number,
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        vendor_tax_id=payload.vendor_tax_id,
        currency=payload.currency,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        received_date=payload.received_date,
        notes=payload.notes,
    )

    # Build lines
    for line_payload in payload.lines:
        line = InvoiceLine(
            line_number=line_payload.line_number,
            description=line_payload.description,
            quantity=line_payload.quantity,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
        )
        invoice.lines.append(line)

    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/",
    response_model=PaginatedResponse[InvoiceResponse],
    summary="List invoices",
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor_code: str | None = Query(None, description="Filter by vendor code"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with optional filtering and pagination."""
    query = select(Invoice).where(Invoice.is_active == True)  # noqa: E712

    if vendor_code:
        query = query.where(Invoice.vendor_code == vendor_code)
    if status_filter:
        query = query.where(Invoice.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    invoices = result.scalars().all()

    items = [InvoiceResponse.model_validate(inv) for inv in invoices]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get a single invoice",
)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Retrieve a single invoice by ID."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
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
    summary="Update an invoice",
)
async def update_invoice(
    invoice_id: UUID,
    payload: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Update invoice fields (status, notes, due_date)."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.flush()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    response_model=SuccessResponse,
    summary="Soft-delete an invoice",
)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Soft-delete an invoice (sets is_active=False)."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    invoice.is_active = False
    await db.flush()
    return SuccessResponse(message=f"Invoice {invoice_id} deleted")
