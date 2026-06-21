// src/api/v1/endpoints/invoices.py
"""Invoice endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import DbSession
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceMatchRequest,
)
from src.schemas.common import PaginationParams, MessageResponse
from src.services.matching_service import MatchingService

router = APIRouter()


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    db: DbSession,
    pagination: PaginationParams = Query(),
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    match_status: Optional[str] = None,
    invoice_number: Optional[str] = None,
    purchase_order_id: Optional[UUID] = None,
):
    """List all invoices with filtering and pagination."""
    query = select(Invoice).where(Invoice.is_deleted == False)

    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
    if status:
        query = query.where(Invoice.status == status)
    if match_status:
        query = query.where(Invoice.match_status == match_status)
    if invoice_number:
        query = query.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if purchase_order_id:
        query = query.where(Invoice.purchase_order_id == purchase_order_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = query.order_by(Invoice.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    query = query.options(selectinload(Invoice.lines))

    result = await db.execute(query)
    items = result.scalars().all()

    return InvoiceListResponse.create(
        items=[InvoiceResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    db: DbSession,
    data: InvoiceCreate,
):
    """Create a new invoice."""
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice with number {data.invoice_number} already exists",
        )

    # Create Invoice
    invoice = Invoice(
        invoice_number=data.invoice_number,
        purchase_order_id=data.purchase_order_id,
        supplier_id=data.supplier_id,
        supplier_name=data.supplier_name,
        supplier_code=data.supplier_code,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        currency=data.currency,
        subtotal=data.subtotal,
        tax_amount=data.tax_amount,
        total_amount=data.total_amount,
        status=data.status,
        match_status=data.match_status,
        match_confidence=data.match_confidence,
        notes=data.notes,
    )

    # Add lines
    for line_data in data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            matched_quantity=line_data.matched_quantity,
            notes=line_data.notes,
        )
        invoice.lines.append(line)

    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    db: DbSession,
    invoice_id: UUID,
):
    """Get an invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .where(Invoice.is_deleted == False)
        .options(selectinload(Invoice.lines))
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    db: DbSession,
    invoice_id: UUID,
    data: InvoiceUpdate,
):
    """Update an invoice."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .where(Invoice.is_deleted == False)
        .options(selectinload(Invoice.lines))
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.flush()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", response_model=MessageResponse)
async def delete_invoice(
    db: DbSession,
    invoice_id: UUID,
):
    """Soft delete an invoice."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .where(Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    from datetime import datetime, timezone
    invoice.is_deleted = True
    invoice.deleted_at = datetime.now(timezone.utc)

    await db.flush()

    return MessageResponse(message="Invoice deleted successfully")


@router.post("/{invoice_id}/match", response_model=dict)
async def match_invoice(
    db: DbSession,
    invoice_id: UUID,
    data: InvoiceMatchRequest,
):
    """Match an invoice against PO and/or DN."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .where(Invoice.is_deleted == False)
        .options(selectinload(Invoice.lines))
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # Perform matching
    matching_service = MatchingService(db)
    match_result = await matching_service.match_invoice(
        invoice=invoice,
        variance_tolerance=data.variance_tolerance,
    )

    return match_result
