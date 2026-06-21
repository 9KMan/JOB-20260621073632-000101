# api/v1/invoices.py
"""Invoice endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ErrorResponse,
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationMeta,
)
from core.database import get_db
from models import Invoice, InvoiceLine, InvoiceStatus

router = APIRouter()

InvoiceDB = Annotated[AsyncSession, get_db]


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: InvoiceDB,
) -> InvoiceResponse:
    """Create a new invoice with line items."""
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(
            Invoice.invoice_number == invoice_data.invoice_number,
            Invoice.is_deleted == False,  # noqa: E712
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists",
        )

    # Create invoice header
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        gross_amount=invoice_data.gross_amount,
        tax_amount=invoice_data.tax_amount,
        net_amount=invoice_data.net_amount,
        currency=invoice_data.currency,
        status=InvoiceStatus.PENDING.value,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        is_credit_memo=invoice_data.is_credit_memo,
        source_system=invoice_data.source_system,
        external_ref=invoice_data.external_ref,
    )

    db.add(invoice)
    await db.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            gross_amount=line_data.gross_amount,
            tax_amount=line_data.tax_amount,
            net_amount=line_data.net_amount,
            po_line_id=line_data.po_line_id,
            delivery_line_id=line_data.delivery_line_id,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceResponse],
)
async def list_invoices(
    db: InvoiceDB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = None,
    status: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> PaginatedResponse[InvoiceResponse]:
    """List invoices with pagination and filters."""
    query = select(Invoice).where(Invoice.is_deleted == False)  # noqa: E712

    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
    if status:
        query = query.where(Invoice.status == status)

    # Count total
    from sqlalchemy import func

    count_query = select(func.count(Invoice.id)).where(
        Invoice.is_deleted == False  # noqa: E712
    )
    if vendor_id:
        count_query = count_query.where(Invoice.vendor_id == vendor_id)
    if status:
        count_query = count_query.where(Invoice.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        data=[InvoiceResponse.model_validate(inv) for inv in invoices],
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_invoice(
    invoice_id: UUID,
    db: InvoiceDB,
) -> InvoiceResponse:
    """Get invoice by ID with line items."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.is_deleted == False,  # noqa: E712
        )
    )
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
    responses={
        404: {"model": ErrorResponse},
    },
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: InvoiceDB,
) -> InvoiceResponse:
    """Update invoice fields."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.is_deleted == False,  # noqa: E712
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update allowed fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)

    await db.commit()
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
    invoice_id: UUID,
    db: InvoiceDB,
) -> None:
    """Soft delete an invoice."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.is_deleted == False,  # noqa: E712
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.soft_delete()
    await db.commit()
