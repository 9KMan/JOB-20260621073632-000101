# api/v1/invoices.py
"""Invoice endpoints."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    ApiResponse,
    ErrorResponse,
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
)
from core.database import get_db
from models.enums import InvoiceStatus, MatchStatus
from models.invoice import Invoice, InvoiceLine
from services.anchoring import AnchoringService
from services.balances import BalanceService
from services.cascade import CascadeService
from services.scoring import ScoringService

router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[InvoiceResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InvoiceResponse]:
    """
    Ingest a new invoice.

    Creates an invoice with line items and triggers the matching process.
    """
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists",
        )

    # Create invoice
    invoice = Invoice(
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency=invoice_data.currency,
        purchase_order_number=invoice_data.purchase_order_number,
        delivery_note_number=invoice_data.delivery_note_number,
        payment_terms=invoice_data.payment_terms,
        description=invoice_data.description,
        raw_data=invoice_data.raw_data,
        status=InvoiceStatus.PENDING,
        match_status=MatchStatus.PENDING,
    )

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            description=line_data.description,
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

    # Load the lines relationship
    await db.refresh(invoice, ["lines"])

    return ApiResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
        message="Invoice created successfully",
    )


@router.get(
    "/",
    response_model=PaginatedResponse[InvoiceListResponse],
)
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vendor_number: str | None = None,
    status: InvoiceStatus | None = None,
    match_status: MatchStatus | None = None,
    invoice_date_from: datetime | None = None,
    invoice_date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[InvoiceListResponse]:
    """
    List all invoices with pagination and filtering.
    """
    query = select(Invoice).where(Invoice.deleted_at.is_(None))

    # Apply filters
    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
    if status:
        query = query.where(Invoice.status == status)
    if match_status:
        query = query.where(Invoice.match_status == match_status)
    if invoice_date_from:
        query = query.where(Invoice.invoice_date >= invoice_date_from.date())
    if invoice_date_to:
        query = query.where(Invoice.invoice_date <= invoice_date_to.date())

    # Count total
    count_query = select(Invoice.id).where(Invoice.deleted_at.is_(None))
    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # Apply pagination
    query = query.order_by(Invoice.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    items = [InvoiceListResponse.model_validate(inv) for inv in invoices]
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{invoice_id}",
    response_model=ApiResponse[InvoiceResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InvoiceResponse]:
    """
    Get a single invoice by ID with all line items.
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return ApiResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
    )


@router.patch(
    "/{invoice_id}",
    response_model=ApiResponse[InvoiceResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InvoiceResponse]:
    """
    Update an invoice's status or metadata.
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)

    # Handle approval
    if update_data.status == InvoiceStatus.APPROVED:
        invoice.approved_at = datetime.now(timezone.utc)
        invoice.approved_by = update_data.approved_by

    await db.flush()
    await db.refresh(invoice, ["lines"])

    return ApiResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
        message="Invoice updated successfully",
    )


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete an invoice.
    """
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.soft_delete()
    await db.flush()
