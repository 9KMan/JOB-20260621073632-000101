// api/routes/invoices.py
"""Invoice routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.security import get_current_active_user
from app.models.user import User
from app.models.invoice import Invoice, InvoiceLine
from api.schemas.documents import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    InvoiceLineResponse,
)

router = APIRouter()


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    po_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all invoices with pagination."""
    query = db.query(Invoice).options(joinedload(Invoice.lines))

    if supplier_id:
        query = query.filter(Invoice.supplier_id == supplier_id)
    if po_id:
        query = query.filter(Invoice.po_id == po_id)
    if status:
        query = query.filter(Invoice.status == status)

    total = query.count()
    invoices = (
        query.order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an invoice by ID."""
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.lines))
        .filter(Invoice.id == invoice_id)
        .first()
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return invoice


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new invoice."""
    # Check for duplicate invoice number
    existing = db.query(Invoice).filter(Invoice.invoice_number == invoice_data.invoice_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice number already exists",
        )

    # Calculate net amount if not provided
    net_amount = invoice_data.net_amount if invoice_data.net_amount else invoice_data.total_amount - invoice_data.tax_amount

    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        net_amount=net_amount,
        currency=invoice_data.currency,
        notes=invoice_data.notes,
        po_id=invoice_data.po_id,
        created_by=current_user.id,
    )
    db.add(invoice)
    db.flush()

    # Create invoice lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.quantity * line_data.unit_price,
            uom=line_data.uom,
        )
        db.add(line)

    db.commit()
    db.refresh(invoice)

    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    db.delete(invoice)
    db.commit()


@router.get("/{invoice_id}/lines", response_model=List[InvoiceLineResponse])
async def get_invoice_lines(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all lines for an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return invoice.lines
