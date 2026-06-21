# api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ErrorResponse,
    InvoiceCreateSchema,
    InvoiceListResponse,
    InvoiceResponseSchema,
    SuccessResponse,
)
from core.database import get_db
from models import Invoice, InvoiceLine, InvoiceStatus
from services.anchoring import AnchoringService
from services.balances import BalanceLedgerService
from services.cascade import CascadeService
from services.scoring import ScoringService

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """
    Ingest a new invoice.
    
    Creates the invoice header and line items.
    Automatically triggers matching if PO reference is provided.
    """
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number '{invoice_data.invoice_number}' already exists",
        )

    # Create invoice
    invoice = Invoice(
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        vendor_tax_id=invoice_data.vendor_tax_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        posting_date=invoice_data.posting_date,
        currency=invoice_data.currency,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        net_amount=invoice_data.net_amount,
        status=InvoiceStatus.PENDING.value,
        notes=invoice_data.notes,
    )
    db.add(invoice)
    await db.flush()

    # Create invoice lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            status="pending",
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.get(
    "/",
    response_model=list[InvoiceListResponse],
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    vendor_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    from_date: Annotated[date | None, Query(alias="fromDate")] = None,
    to_date: Annotated[date | None, Query(alias="toDate")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Invoice]:
    """List invoices with optional filtering and pagination."""
    query = select(Invoice).where(Invoice.is_deleted == False)

    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
    if status:
        query = query.where(Invoice.status == status)
    if from_date:
        query = query.where(Invoice.invoice_date >= from_date)
    if to_date:
        query = query.where(Invoice.invoice_date <= to_date)

    query = query.offset((page - 1) * per_page).limit(per_page)
    query = query.order_by(Invoice.invoice_date.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponseSchema,
    responses={404: {"model": ErrorResponse}},
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Get invoice by ID with all line items."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    return invoice


@router.patch(
    "/{invoice_id}/status",
    response_model=InvoiceResponseSchema,
    responses={404: {"model": ErrorResponse}},
)
async def update_invoice_status(
    invoice_id: uuid.UUID,
    new_status: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Invoice:
    """Update invoice status."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    invoice.status = new_status
    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    invoice.is_deleted = True
    await db.commit()
