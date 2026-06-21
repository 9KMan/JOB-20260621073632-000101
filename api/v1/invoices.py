// api/v1/invoices.py
"""Invoice ingestion and CRUD endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationParams,
    ErrorResponse,
)
from core.database import get_db_session
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceResponse:
    """
    Ingest a new invoice.

    Creates an invoice header and its associated line items.
    """
    # Check for duplicate invoice
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

    # Create invoice
    invoice = Invoice(
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        vendor_tax_id=invoice_data.vendor_tax_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        invoice_amount=invoice_data.invoice_amount,
        tax_amount=invoice_data.tax_amount,
        currency_code=invoice_data.currency_code,
        description=invoice_data.description,
        payment_terms=invoice_data.payment_terms,
        status=InvoiceStatus.PENDING,
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
            line_amount=line_data.line_amount,
            po_line_id=uuid.UUID(line_data.po_line_id) if line_data.po_line_id else None,
            dn_line_id=uuid.UUID(line_data.dn_line_id) if line_data.dn_line_id else None,
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    pagination: Annotated[PaginationParams, Query()],
    vendor_number: Annotated[str | None, Query(description="Filter by vendor")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    invoice_date_from: Annotated[str | None, Query(description="Filter from date (YYYY-MM-DD)")] = None,
    invoice_date_to: Annotated[str | None, Query(description="Filter to date (YYYY-MM-DD)")] = None,
) -> PaginatedResponse[InvoiceResponse]:
    """
    List all invoices with pagination and filtering.
    """
    query = select(Invoice).where(Invoice.is_deleted == False)
    count_query = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)

    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
        count_query = count_query.where(Invoice.vendor_number == vendor_number)

    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)

    # Get total count
    total = (await db.execute(count_query)).scalar_one()

    # Get paginated results
    query = query.offset(pagination.offset).limit(pagination.limit)
    query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    items = [InvoiceResponse.model_validate(inv) for inv in invoices]
    return PaginatedResponse.create(items, total, pagination)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceResponse:
    """
    Get a single invoice by ID.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(invoice_id),
            Invoice.is_deleted == False,
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
    invoice_id: str,
    update_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceResponse:
    """
    Update an invoice.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(invoice_id),
            Invoice.is_deleted == False,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

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
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Soft delete an invoice.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(invoice_id),
            Invoice.is_deleted == False,
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
