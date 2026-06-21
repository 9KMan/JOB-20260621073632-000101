# app/api/invoices.py
"""Invoice API endpoints."""
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
)

router = APIRouter()


def calculate_invoice_totals(invoice: Invoice) -> None:
    """Calculate invoice subtotal, tax, and total amounts."""
    subtotal = Decimal("0")
    tax_amount = Decimal("0")
    for line in invoice.lines:
        line.calculate_line_total()
        line_total = line.quantity * line.unit_price
        subtotal += line_total
        tax_amount += line_total * line.tax_rate
    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total_amount = subtotal + tax_amount + invoice.shipping_cost


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Create a new invoice with line items."""
    # Check if invoice number already exists
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice with number '{invoice_data.invoice_number}' already exists",
        )

    # Create invoice
    invoice_dict = invoice_data.model_dump(exclude={"lines"})
    invoice = Invoice(**invoice_dict)

    # Create lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(**line_data.model_dump())
        line.calculate_line_total()
        invoice.lines.append(line)

    # Calculate totals
    calculate_invoice_totals(invoice)

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    # Reload with lines
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    return InvoiceResponse.model_validate(invoice)


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    invoice_number: Optional[str] = Query(None, description="Search by invoice number"),
) -> InvoiceListResponse:
    """List all invoices with pagination and filtering."""
    query = select(Invoice).options(selectinload(Invoice.lines))
    count_query = select(func.count(Invoice.id))

    # Apply filters
    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
        count_query = count_query.where(Invoice.vendor_id == vendor_id)
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)
    if invoice_number:
        inv_filter = Invoice.invoice_number.ilike(f"%{invoice_number}%")
        query = query.where(inv_filter)
        count_query = count_query.where(inv_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Get an invoice by ID with line items."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )
    return InvoiceResponse.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
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
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    # Check if invoice is in editable status
    if invoice.status not in [InvoiceStatus.DRAFT.value, InvoiceStatus.SUBMITTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update invoice in '{invoice.status}' status",
        )

    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an invoice (soft delete by setting status to cancelled)."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )

    if invoice.status not in [InvoiceStatus.DRAFT.value, InvoiceStatus.SUBMITTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete invoice in '{invoice.status}' status",
        )

    invoice.status = InvoiceStatus.CANCELLED.value
    await db.commit()
