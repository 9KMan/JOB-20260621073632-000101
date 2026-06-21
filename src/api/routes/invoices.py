// src/api/routes/invoices.py
"""Invoice API routes."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.deps import DBSession, CurrentUser
from models.invoice import Invoice, InvoiceLine
from models.user import User

router = APIRouter()


# Pydantic Schemas
class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line."""

    line_number: int
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity_invoiced: Decimal = Field(ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating Invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice line response."""

    id: str
    line_total: Decimal

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""

    invoice_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: str
    purchase_order_id: Optional[str] = None
    po_number: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating Invoice."""

    subtotal: Decimal
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    """Schema for updating Invoice."""

    due_date: Optional[date] = None
    status: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""

    id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_deleted: bool
    created_at: str
    updated_at: str
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for Invoice list response."""

    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> Invoice:
    """Create a new Invoice."""
    # Check if invoice number already exists
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_in.invoice_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice {invoice_in.invoice_number} already exists",
        )

    # Create Invoice
    invoice = Invoice(
        invoice_number=invoice_in.invoice_number,
        supplier_id=uuid.UUID(invoice_in.supplier_id),
        supplier_name=invoice_in.supplier_name,
        supplier_code=invoice_in.supplier_code,
        purchase_order_id=uuid.UUID(invoice_in.purchase_order_id) if invoice_in.purchase_order_id else None,
        po_number=invoice_in.po_number,
        invoice_date=invoice_in.invoice_date,
        due_date=invoice_in.due_date,
        subtotal=invoice_in.subtotal,
        tax_amount=invoice_in.tax_amount,
        total_amount=invoice_in.total_amount,
        currency=invoice_in.currency,
        payment_terms=invoice_in.payment_terms,
        notes=invoice_in.notes,
        status="RECEIVED",
    )
    db.add(invoice)
    await db.flush()

    # Create lines
    for line_in in invoice_in.lines:
        line_total = line_in.quantity_invoiced * line_in.unit_price
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_in.line_number,
            product_code=line_in.product_code,
            product_name=line_in.product_name,
            description=line_in.description,
            quantity_invoiced=line_in.quantity_invoiced,
            unit_of_measure=line_in.unit_of_measure,
            unit_price=line_in.unit_price,
            line_total=line_total,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_code: Optional[str] = None,
    status: Optional[str] = None,
    invoice_number: Optional[str] = None,
    po_number: Optional[str] = None,
) -> dict:
    """List Invoices with pagination."""
    query = select(Invoice).where(Invoice.is_deleted == False)

    if supplier_code:
        query = query.where(Invoice.supplier_code == supplier_code)
    if status:
        query = query.where(Invoice.status == status)
    if invoice_number:
        query = query.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if po_number:
        query = query.where(Invoice.po_number == po_number)

    # Get total count
    count_result = await db.execute(
        select(Invoice.id).where(Invoice.is_deleted == False)
    )
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.options(selectinload(Invoice.lines))
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> Invoice:
    """Get an Invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    invoice_in: InvoiceUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> Invoice:
    """Update an Invoice."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    update_data = invoice_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft delete an Invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    invoice.is_deleted = True
    invoice.deleted_at = date.today()
    await db.commit()
