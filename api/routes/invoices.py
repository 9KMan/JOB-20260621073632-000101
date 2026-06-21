// api/routes/invoices.py
"""Invoice routes."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from api.deps import get_current_user, require_role
from api.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetailResponse,
)
from core.database import get_db
from models.user import User
from models.invoice import Invoice, InvoiceLine, InvoiceStatus

router = APIRouter()


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    po_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Invoice]:
    """
    List all invoices with optional filtering.
    """
    query = db.query(Invoice)
    
    if supplier_id:
        query = query.filter(Invoice.supplier_id == supplier_id)
    if status:
        query = query.filter(Invoice.status == status)
    if po_id:
        query = query.filter(Invoice.po_id == po_id)
    
    return query.offset(skip).limit(limit).all()


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """
    Get an invoice by ID with all lines.
    """
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines)
    ).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice


@router.post("/", response_model=InvoiceDetailResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> Invoice:
    """
    Create a new invoice with lines.
    """
    # Check for duplicate invoice number
    existing = db.query(Invoice).filter(
        Invoice.invoice_number == invoice_data.invoice_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice with number '{invoice_data.invoice_number}' already exists",
        )
    
    # Create invoice
    invoice_dict = invoice_data.model_dump(exclude={"lines"})
    invoice = Invoice(**invoice_dict)
    
    # Create lines
    for line_data in invoice_data.lines:
        line_dict = line_data.model_dump()
        line = InvoiceLine(**line_dict)
        line.calculate_totals()
        invoice.lines.append(line)
    
    # Calculate totals
    invoice.calculate_totals()
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceDetailResponse)
def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "accountant")),
) -> Invoice:
    """
    Update an invoice.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    """
    Delete an invoice.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    
    if invoice.status not in [InvoiceStatus.DRAFT.value, InvoiceStatus.SUBMITTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete draft or submitted invoices",
        )
    
    db.delete(invoice)
    db.commit()
