# api/v1/invoices.py
"""Invoice API endpoints.

Provides CRUD operations and matching trigger for invoices.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    PaginatedResponse,
    ErrorResponse,
    BaseFilterParams,
)
from core.database import get_db
from models.invoice import Invoice, InvoiceLine
from models.enums import InvoiceStatus, MatchingStatus
from services.anchoring import AnchoringService
from services.cascade import CascadeService

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Create a new invoice.

    Ingests a new invoice with line items. Triggers automatic matching
    if configured.
    """
    # Check for duplicate invoice
    existing = await db.execute(
        select(Invoice).where(
            Invoice.invoice_number == invoice_data.invoice_number,
            Invoice.supplier_id == invoice_data.supplier_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice {invoice_data.invoice_number} already exists for supplier",
        )

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount or 0,
        currency=invoice_data.currency,
        status=InvoiceStatus.PENDING,
        matching_status=MatchingStatus.PENDING,
        notes=invoice_data.notes,
        created_by=invoice_data.created_by,
    )
    db.add(invoice)
    await db.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    # Load lines for response
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceResponse],
)
async def list_invoices(
    params: Annotated[BaseFilterParams, Query()],
    status: str | None = Query(None, description="Filter by status"),
    matching_status: str | None = Query(None, description="Filter by matching status"),
    supplier_id: str | None = Query(None, description="Filter by supplier"),
    invoice_date_from: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    invoice_date_to: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[InvoiceResponse]:
    """List invoices with filtering and pagination."""
    query = select(Invoice).options(selectinload(Invoice.lines))

    # Apply filters
    if status:
        query = query.where(Invoice.status == status)
    if matching_status:
        query = query.where(Invoice.matching_status == matching_status)
    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
    if invoice_date_from:
        query = query.where(Invoice.invoice_date >= invoice_date_from)
    if invoice_date_to:
        query = query.where(Invoice.invoice_date <= invoice_date_to)

    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply sorting
    if params.sort_by:
        sort_column = getattr(Invoice, params.sort_by, Invoice.created_at)
        if params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(Invoice.created_at.desc())

    # Apply pagination
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    return PaginatedResponse.create(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Get invoice by ID with all line items."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
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
    responses={404: {"model": ErrorResponse}},
)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Update invoice fields."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    await db.delete(invoice)
    await db.commit()
