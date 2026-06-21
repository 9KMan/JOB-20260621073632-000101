// api/v1/invoices.py
"""Invoice API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.config import settings
from models.invoice import Invoice, InvoiceLineItem
from models.enums import InvoiceStatus
from api.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetailResponse,
    PaginatedResponse,
    PaginationMeta,
)

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: DB,
) -> Invoice:
    """Ingest a new invoice into the system.
    
    Creates a new invoice with optional line items.
    The invoice will be in PENDING status until matched.
    """
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number {invoice_data.invoice_number} already exists",
        )
    
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        currency=invoice_data.currency,
        status=InvoiceStatus.PENDING,
        notes=invoice_data.notes,
        erp_reference=invoice_data.erp_reference,
    )
    db.add(invoice)
    await db.flush()
    
    # Create line items
    for item_data in invoice_data.line_items:
        line_item = InvoiceLineItem(
            invoice_id=invoice.id,
            line_number=item_data.line_number,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            amount=item_data.amount,
            uom=item_data.uom,
            tax_code=item_data.tax_code,
        )
        db.add(line_item)
    
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceResponse],
    summary="List all invoices",
)
async def list_invoices(
    db: DB,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    supplier_id: str | None = Query(None, description="Filter by supplier"),
    status: InvoiceStatus | None = Query(None, description="Filter by status"),
    from_date: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with optional filters and pagination."""
    # Build base query
    query = select(Invoice)
    count_query = select(func.count(Invoice.id))
    
    # Apply filters
    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
        count_query = count_query.where(Invoice.supplier_id == supplier_id)
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)
    if from_date:
        query = query.where(Invoice.invoice_date >= from_date)
        count_query = count_query.where(Invoice.invoice_date >= from_date)
    if to_date:
        query = query.where(Invoice.invoice_date <= to_date)
        count_query = count_query.where(Invoice.invoice_date <= to_date)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Invoice.created_at.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size
    meta = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    
    return PaginatedResponse(data=list(invoices), meta=meta)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceDetailResponse,
    summary="Get invoice details",
)
async def get_invoice(
    invoice_id: UUID,
    db: DB,
) -> Invoice:
    """Get detailed invoice information including line items."""
    query = (
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with id {invoice_id} not found",
        )
    
    return invoice


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update invoice",
)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: DB,
) -> Invoice:
    """Update invoice status or other fields."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with id {invoice_id} not found",
        )
    
    # Update allowed fields
    if invoice_data.status:
        invoice.status = InvoiceStatus(invoice_data.status)
    if invoice_data.notes is not None:
        invoice.notes = invoice_data.notes
    if invoice_data.match_decision:
        invoice.match_decision = invoice_data.match_decision
    
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
)
async def delete_invoice(
    invoice_id: UUID,
    db: DB,
) -> None:
    """Delete an invoice (soft delete in production)."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with id {invoice_id} not found",
        )
    
    await db.delete(invoice)
    await db.commit()
