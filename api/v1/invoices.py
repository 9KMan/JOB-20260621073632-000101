# api/v1/invoices.py
"""Invoice endpoints for ingestion and CRUD operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    ErrorResponse,
)
from core.database import get_db
from models import Invoice, InvoiceLine, InvoiceStatus

router = APIRouter()


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
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Create a new invoice with lines."""
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists",
        )

    invoice = Invoice(
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        currency=invoice_data.currency,
        status=InvoiceStatus.DRAFT.value,
        notes=invoice_data.notes,
        source_system=invoice_data.source_system,
        external_reference=invoice_data.external_reference,
        is_credit_memo=invoice_data.is_credit_memo,
    )

    for line_data in invoice_data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
        )
        invoice.lines.append(line)

    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceResponse],
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    vendor_number: str | None = Query(None, description="Filter by vendor number"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    from_date: str | None = Query(None, alias="from_date", description="Filter from date"),
    to_date: str | None = Query(None, alias="to_date", description="Filter to date"),
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with pagination and filters."""
    query = select(Invoice).where(Invoice.is_deleted == False)
    count_query = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)

    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
        count_query = count_query.where(Invoice.vendor_number == vendor_number)

    if status_filter:
        query = query.where(Invoice.status == status_filter)
        count_query = count_query.where(Invoice.status == status_filter)

    query = query.offset(pagination.offset).limit(pagination.page_size)
    query = query.order_by(Invoice.invoice_date.desc())

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    invoices_list = result.scalars().all()
    total = count_result.scalar() or 0

    return PaginatedResponse.create(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices_list],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Get a specific invoice by ID."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/{invoice_id}/status",
    response_model=InvoiceResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_invoice_status(
    invoice_id: str,
    new_status: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceResponse:
    """Update invoice status."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    try:
        InvoiceStatus(new_status)
    except ValueError:
        valid_statuses = [s.value for s in InvoiceStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Valid values: {valid_statuses}",
        )

    invoice.status = new_status
    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Soft delete an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.is_deleted = True
    invoice.deleted_at = func.now()
    await db.flush()

    return SuccessResponse(
        success=True,
        message=f"Invoice {invoice_id} deleted successfully",
    )
