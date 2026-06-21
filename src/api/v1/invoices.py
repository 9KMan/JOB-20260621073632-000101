# src/api/v1/invoices.py
"""Invoice endpoints for ingestion and CRUD operations."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationMeta,
)
from core.database import get_db_session
from models.invoice import Invoice, InvoiceLine
from models.enums import InvoiceStatus

router = APIRouter()


async def get_pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> tuple[int, int]:
    """Get pagination parameters."""
    return page, per_page


async def paginate_query(
    query,
    session: AsyncSession,
    page: int,
    per_page: int,
) -> tuple[list, int]:
    """Execute paginated query and return items with total count."""
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    offset = (page - 1) * per_page
    paginated_query = query.offset(offset).limit(per_page)
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    return list(items), total


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new invoice",
    description="Create a new invoice with optional line items.",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Ingest a new invoice.
    
    Creates an invoice record with associated line items.
    The invoice status will be set to 'pending' upon creation.
    """
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        vendor_reference=invoice_data.vendor_reference,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        metadata_json=invoice_data.metadata,
        status=InvoiceStatus.PENDING.value,
    )
    
    # Add line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            description=line_data.description,
            product_code=line_data.product_code,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            tax_code=line_data.tax_code,
            tax_rate=line_data.tax_rate,
            line_total=line_data.line_total,
            po_line_id=line_data.po_line_id,
            delivery_line_id=line_data.delivery_line_id,
            match_status="unmatched",
        )
        invoice.lines.append(line)
    
    session.add(invoice)
    await session.flush()
    await session.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceResponse],
    summary="List invoices",
    description="Get a paginated list of invoices with optional filtering.",
)
async def list_invoices(
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    supplier_id: str | None = None,
    invoice_date_from: datetime | None = None,
    invoice_date_to: datetime | None = None,
) -> PaginatedResponse[InvoiceResponse]:
    """
    List all invoices with optional filters.
    
    - **status**: Filter by invoice status
    - **supplier_id**: Filter by supplier ID
    - **invoice_date_from**: Filter invoices from this date
    - **invoice_date_to**: Filter invoices until this date
    """
    # Build query
    query = select(Invoice).options(selectinload(Invoice.lines))
    
    # Apply filters
    conditions = []
    if status:
        conditions.append(Invoice.status == status)
    if supplier_id:
        conditions.append(Invoice.supplier_id == supplier_id)
    if invoice_date_from:
        conditions.append(Invoice.invoice_date >= invoice_date_from.date())
    if invoice_date_to:
        conditions.append(Invoice.invoice_date <= invoice_date_to.date())
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Invoice.created_at.desc())
    
    # Execute paginated query
    items, total = await paginate_query(query, session, page, per_page)
    
    # Build response
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice by ID",
    description="Retrieve a single invoice with its line items.",
)
async def get_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Get a specific invoice by ID.
    
    Returns the invoice with all associated line items.
    """
    query = select(Invoice).options(
        selectinload(Invoice.lines)
    ).where(Invoice.id == invoice_id)
    
    result = await session.execute(query)
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
    summary="Update invoice",
    description="Update invoice fields such as status or notes.",
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Update an existing invoice.
    
    Only provided fields will be updated.
    """
    query = select(Invoice).options(
        selectinload(Invoice.lines)
    ).where(Invoice.id == invoice_id)
    
    result = await session.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "metadata":
            invoice.metadata_json = value
        else:
            setattr(invoice, field, value)
    
    await session.flush()
    await session.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
    description="Soft delete an invoice.",
)
async def delete_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Soft delete an invoice.
    
    The invoice will be marked as deleted but not removed from the database.
    """
    query = select(Invoice).where(Invoice.id == invoice_id)
    
    result = await session.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    invoice.deleted_at = datetime.utcnow()
    invoice.status = InvoiceStatus.CANCELLED.value
    
    await session.flush()


__all__ = ["router"]
