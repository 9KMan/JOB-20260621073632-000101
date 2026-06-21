# api/v1/invoices.py
"""Invoice API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_async_session
from models import Invoice, InvoiceLine
from models.enums import InvoiceStatus, MatchStatus
from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationParams,
    ErrorResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Duplicate invoice"},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> InvoiceResponse:
    """Ingest a new invoice.

    Creates a new invoice with associated line items.
    The invoice will be in PENDING status and ready for matching.
    """
    # Check for duplicate invoice number
    stmt = select(Invoice).where(
        Invoice.invoice_number == invoice_data.invoice_number,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number '{invoice_data.invoice_number}' already exists",
        )

    # Create invoice
    invoice = Invoice(
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        vendor_tax_id=invoice_data.vendor_tax_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        currency_code=invoice_data.currency_code,
        description=invoice_data.description,
        payment_terms=invoice_data.payment_terms,
        erp_invoice_id=invoice_data.erp_invoice_id,
        po_id=invoice_data.po_id,
        delivery_note_id=invoice_data.delivery_note_id,
        status=InvoiceStatus.PENDING,
        match_status=MatchStatus.PENDING,
    )
    session.add(invoice)
    await session.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            product_code=line_data.product_code,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            po_line_id=line_data.po_line_id,
            delivery_note_line_id=line_data.delivery_note_line_id,
        )
        session.add(line)

    await session.commit()
    await session.refresh(invoice)

    # Load lines
    stmt = select(Invoice).options(selectinload(Invoice.lines)).where(
        Invoice.id == invoice.id
    )
    result = await session.execute(stmt)
    invoice = result.scalar_one()

    return InvoiceResponse.model_validate(invoice)


@router.get("", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    pagination: Annotated[PaginationParams, Depends()],
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status: InvoiceStatus | None = Query(None, description="Filter by status"),
    invoice_date_from: str | None = Query(None, description="Filter by invoice date (from)"),
    invoice_date_to: str | None = Query(None, description="Filter by invoice date (to)"),
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with pagination and filtering."""
    # Build query
    stmt = select(Invoice).where(Invoice.is_deleted == False)  # noqa: E712

    if vendor_number:
        stmt = stmt.where(Invoice.vendor_number == vendor_number)
    if status:
        stmt = stmt.where(Invoice.status == status)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Get paginated results
    stmt = stmt.options(selectinload(Invoice.lines))
    stmt = stmt.order_by(Invoice.created_at.desc())
    stmt = stmt.offset(pagination.skip).limit(pagination.limit)

    result = await session.execute(stmt)
    invoices = result.scalars().all()

    items = [InvoiceResponse.model_validate(inv) for inv in invoices]
    has_more = (pagination.skip + len(items)) < total

    return PaginatedResponse(
        items=items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        has_more=has_more,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> InvoiceResponse:
    """Get a single invoice by ID."""
    stmt = select(Invoice).options(selectinload(Invoice.lines)).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await session.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> InvoiceResponse:
    """Update an invoice."""
    stmt = select(Invoice).options(selectinload(Invoice.lines)).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await session.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)

    await session.commit()
    await session.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Soft delete an invoice."""
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,  # noqa: E712
    )
    result = await session.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    invoice.soft_delete()
    await session.commit()
