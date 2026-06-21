# src/api/v1/routes/invoices.py
"""Invoice routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.dependencies import get_current_active_user
from src.models.user import User
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.api.v1.schemas.invoices import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetailResponse,
)

router = APIRouter()


@router.post("/", response_model=InvoiceDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Invoice:
    """Create a new invoice."""
    # Check for duplicate invoice number
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice {invoice_data.invoice_number} already exists",
        )

    # Calculate totals
    subtotal = sum(line.line_total for line in invoice_data.lines)
    tax_amount = sum(line.tax_amount for line in invoice_data.lines)
    total_amount = subtotal + tax_amount

    # Create Invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        supplier_reference=invoice_data.supplier_reference,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        po_reference=invoice_data.po_reference,
        currency=invoice_data.currency,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        notes=invoice_data.notes,
        status=InvoiceStatus.PENDING.value,
    )

    # Add lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            item_description=line_data.item_description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            purchase_order_line_id=line_data.purchase_order_line_id,
            delivery_note_line_id=line_data.delivery_note_line_id,
        )
        invoice.lines.append(line)

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    supplier_id: str | None = None,
    status: str | None = None,
) -> list[Invoice]:
    """List all invoices with pagination."""
    query = select(Invoice).where(Invoice.is_active == True)

    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
    if status:
        query = query.where(Invoice.status == status)

    query = query.offset(skip).limit(limit).order_by(Invoice.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Invoice:
    """Get an invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
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
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Invoice:
    """Update an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Soft delete an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    invoice.is_active = False
    await db.commit()
