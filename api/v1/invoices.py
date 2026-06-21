# api/v1/invoices.py
"""Invoice endpoints for ingestion and CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models import Invoice, InvoiceLine
from api.schemas import (
    BaseResponse,
    PaginatedResponse,
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    InvoiceLineResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=BaseResponse[InvoiceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new invoice",
    description="Create a new invoice with line items. Automatically triggers matching.",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[InvoiceResponse]:
    """Ingest a new invoice."""
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
        invoice_number=invoice_data.invoice_number,
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        tax_exclusive=invoice_data.tax_exclusive,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        purchase_order_id=invoice_data.purchase_order_id,
        source_system=invoice_data.source_system,
        metadata_=invoice_data.metadata,
        status="pending",
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
            net_amount=line_data.net_amount,
            tax_amount=line_data.tax_amount,
            tax_rate=line_data.tax_rate,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(invoice)
    
    # Load lines relationship
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()
    
    return BaseResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
        message="Invoice created successfully",
    )


@router.get(
    "/",
    response_model=PaginatedResponse[InvoiceResponse],
    summary="List invoices",
    description="Get paginated list of invoices with optional filters.",
)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    vendor_id: str | None = None,
    status: str | None = None,
    match_decision: str | None = None,
    invoice_date_from: str | None = None,
    invoice_date_to: str | None = None,
) -> PaginatedResponse[InvoiceResponse]:
    """List invoices with pagination and filters."""
    query = select(Invoice).options(selectinload(Invoice.lines))
    count_query = select(func.count(Invoice.id))
    
    # Apply filters
    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
        count_query = count_query.where(Invoice.vendor_id == vendor_id)
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)
    if match_decision:
        query = query.where(Invoice.match_decision == match_decision)
        count_query = count_query.where(Invoice.match_decision == match_decision)
    
    # Get total count
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    pages = (total + per_page - 1) // per_page if total else 1
    
    return PaginatedResponse(
        success=True,
        data=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/{invoice_id}",
    response_model=BaseResponse[InvoiceResponse],
    summary="Get invoice by ID",
)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[InvoiceResponse]:
    """Get a single invoice by ID."""
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
    
    return BaseResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
    )


@router.patch(
    "/{invoice_id}",
    response_model=BaseResponse[InvoiceResponse],
    summary="Update invoice",
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[InvoiceResponse]:
    """Update an invoice."""
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
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)
    
    await db.commit()
    await db.refresh(invoice)
    
    return BaseResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
        message="Invoice updated successfully",
    )


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Soft delete an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    invoice.is_deleted = True
    invoice.deleted_at = func.now()
    await db.commit()
