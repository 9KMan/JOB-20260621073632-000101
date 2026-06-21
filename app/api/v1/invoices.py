// app/api/v1/invoices.py
"""Invoice API endpoints."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginationParams,
    create_pagination_response,
    PaginatedResponse,
)
from app.core.database import get_db_session
from app.models import Invoice, InvoiceLine
from app.models.enums import InvoiceStatus


router = APIRouter()


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Create a new invoice with line items.
    
    Args:
        invoice_data: Invoice data including line items
        db: Database session
        
    Returns:
        Created invoice with lines
    """
    # Check for duplicate invoice number
    stmt = select(Invoice).where(
        Invoice.invoice_number == invoice_data.invoice_number,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number {invoice_data.invoice_number} already exists",
        )
    
    # Create invoice
    invoice = Invoice(
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        vendor_tax_id=invoice_data.vendor_tax_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        receipt_date=invoice_data.receipt_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency_code=invoice_data.currency_code,
        purchase_order_ref=invoice_data.purchase_order_ref,
        delivery_note_ref=invoice_data.delivery_note_ref,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        source_system=invoice_data.source_system,
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
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            unit_of_measure=line_data.unit_of_measure,
            quantity=line_data.quantity,
            quantity_received=line_data.quantity_received,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            po_line_ref=line_data.po_line_ref,
            dn_line_ref=line_data.dn_line_ref,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.get("/", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    pagination: PaginationParams = Depends(),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    has_exception: Optional[bool] = Query(None, description="Filter by exception flag"),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[InvoiceResponse]:
    """
    List invoices with pagination and filtering.
    
    Args:
        pagination: Pagination parameters
        vendor_id: Optional vendor filter
        status_filter: Optional status filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        has_exception: Optional exception flag filter
        db: Database session
        
    Returns:
        Paginated list of invoices
    """
    # Build query
    stmt = select(Invoice).where(Invoice.is_deleted == False)
    count_stmt = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)
    
    # Apply filters
    if vendor_id:
        stmt = stmt.where(Invoice.vendor_id == vendor_id)
        count_stmt = count_stmt.where(Invoice.vendor_id == vendor_id)
    
    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
        count_stmt = count_stmt.where(Invoice.status == status_filter)
    
    if date_from:
        stmt = stmt.where(Invoice.invoice_date >= date_from)
        count_stmt = count_stmt.where(Invoice.invoice_date >= date_from)
    
    if date_to:
        stmt = stmt.where(Invoice.invoice_date <= date_to)
        count_stmt = count_stmt.where(Invoice.invoice_date <= date_to)
    
    if has_exception is not None:
        stmt = stmt.where(Invoice.has_exception == has_exception)
        count_stmt = count_stmt.where(Invoice.has_exception == has_exception)
    
    # Get total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination
    stmt = stmt.order_by(Invoice.created_at.desc())
    stmt = stmt.offset(pagination.offset).limit(pagination.page_size)
    
    result = await db.execute(stmt)
    invoices = result.scalars().all()
    
    # Convert to response models
    items = [InvoiceResponse.model_validate(inv) for inv in invoices]
    
    return create_pagination_response(items, total, pagination.page, pagination.page_size)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Get a single invoice by ID.
    
    Args:
        invoice_id: Invoice UUID
        db: Database session
        
    Returns:
        Invoice with line items
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    update_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    """
    Update an invoice.
    
    Args:
        invoice_id: Invoice UUID
        update_data: Fields to update
        db: Database session
        
    Returns:
        Updated invoice
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    # Update fields
    if update_data.status:
        invoice.status = InvoiceStatus(update_data.status)
    if update_data.notes is not None:
        invoice.notes = update_data.notes
    if update_data.due_date is not None:
        invoice.due_date = update_data.due_date
    
    await db.commit()
    await db.refresh(invoice)
    
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Soft delete an invoice.
    
    Args:
        invoice_id: Invoice UUID
        db: Database session
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    invoice.soft_delete()
    await db.commit()
