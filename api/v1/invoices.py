# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    PaginatedResponse,
    PageParams,
)
from core.database import get_db
from core.security import get_current_user_id
from models import Invoice, InvoiceLine, InvoiceStatus

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
)
async def ingest_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> InvoiceResponse:
    """Ingest a new invoice with its line items."""
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice.id).where(Invoice.invoice_number == payload.invoice_number)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice number '{payload.invoice_number}' already exists",
        )

    invoice = Invoice(
        vendor_code=payload.vendor_code,
        vendor_name=payload.vendor_name,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        currency=payload.currency,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        status=InvoiceStatus.DRAFT,
        erp_invoice_id=payload.erp_invoice_id,
        raw_payload=payload.raw_payload,
    )
    db.add(invoice)
    await db.flush()

    for line_payload in payload.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_payload.line_number,
            description=line_payload.description,
            product_code=line_payload.product_code,
            product_name=line_payload.product_name,
            quantity=line_payload.quantity,
            unit_of_measure=line_payload.unit_of_measure,
            unit_price=line_payload.unit_price,
            line_amount=line_payload.line_amount,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)


@router.get("/", response_model=PaginatedResponse)
async def list_invoices(
    params: PageParams = Depends(),
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    vendor_code: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> PaginatedResponse:
    """List all invoices with optional filtering and pagination."""
    stmt = select(Invoice)
    count_stmt = select(func.count(Invoice.id))

    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
        count_stmt = count_stmt.where(Invoice.status == status_filter)
    if vendor_code:
        stmt = stmt.where(Invoice.vendor_code == vendor_code)
        count_stmt = count_stmt.where(Invoice.vendor_code == vendor_code)

    # Total count
    total = (await db.execute(count_stmt)).scalar_one()
    # Paginated rows
    stmt = stmt.order_by(Invoice.created_at.desc()).offset(params.offset).limit(params.page_size)
    rows = (await db.execute(stmt)).scalars().all()

    items = [InvoiceListResponse.model_validate(r) for r in rows]
    return PaginatedResponse.create(items, total, params)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> InvoiceResponse:
    """Retrieve a single invoice with its line items."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> InvoiceResponse:
    """Update the status of an existing invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    new_status = payload.get("status")
    if new_status is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field 'status' is required",
        )

    try:
        invoice.status = InvoiceStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{new_status}'",
        )

    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice)
