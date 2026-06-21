// src/api/routes/invoices.py
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models.user import User
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.api.routes.auth import get_current_user
from src.api.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse
)

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invoice."""
    existing_invoice = db.query(Invoice).filter(
        Invoice.invoice_number == invoice_data.invoice_number
    ).first()
    
    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice with number {invoice_data.invoice_number} already exists"
        )
    
    # Calculate totals
    line_items = []
    subtotal = 0
    tax_total = 0
    
    for line_data in invoice_data.line_items:
        line_total = line_data.quantity * line_data.unit_price
        tax_amount = line_total * line_data.tax_rate
        subtotal += line_total
        tax_total += tax_amount
        
        line_items.append(InvoiceLine(
            line_number=line_data.line_number,
            item_code=line_data.item_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_total,
            tax_rate=line_data.tax_rate,
            tax_amount=tax_amount,
            matched_po_line_id=line_data.matched_po_line_id,
            created_by=current_user.id
        ))
    
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        supplier_code=invoice_data.supplier_code,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=subtotal,
        tax_amount=tax_total,
        total_amount=subtotal + tax_total,
        currency=invoice_data.currency,
        notes=invoice_data.notes,
        payment_terms=invoice_data.payment_terms,
        status=InvoiceStatus.PENDING,
        created_by=current_user.id
    )
    
    for line in line_items:
        invoice.line_items.append(line)
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.get("/", response_model=InvoiceListResponse)
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: UUID | None = None,
    status_filter: InvoiceStatus | None = None,
    search: str | None = None
):
    """List all invoices with pagination."""
    query = db.query(Invoice).options(joinedload(Invoice.line_items))
    
    if supplier_id:
        query = query.filter(Invoice.supplier_id == supplier_id)
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Invoice.invoice_number.ilike(search_term) |
            Invoice.supplier_name.ilike(search_term)
        )
    
    total = query.count()
    items = query.order_by(Invoice.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return InvoiceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an invoice by ID."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.line_items)
    ).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    invoice.updated_by = current_user.id
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an invoice (only if not approved/paid)."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.status in [InvoiceStatus.APPROVED, InvoiceStatus.PAID]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an approved or paid invoice"
        )
    
    db.delete(invoice)
    db.commit()
