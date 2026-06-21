// src/api/routes/invoices.py
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.api.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse
)

router = APIRouter()


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Invoice).filter(
        Invoice.invoice_number == invoice_data.invoice_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice with number {invoice_data.invoice_number} already exists"
        )
    
    subtotal = sum(line.unit_price * line.quantity for line in invoice_data.lines)
    tax_amount = subtotal * Decimal("0.10")
    total_amount = subtotal + tax_amount
    
    db_invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_code=invoice_data.supplier_code,
        supplier_name=invoice_data.supplier_name,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        purchase_order_id=invoice_data.purchase_order_id,
        currency=invoice_data.currency,
        notes=invoice_data.notes,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status=InvoiceStatus.SUBMITTED
    )
    db.add(db_invoice)
    db.flush()
    
    for line_data in invoice_data.lines:
        line_total = line_data.unit_price * line_data.quantity
        db_line = InvoiceLine(
            invoice_id=db_invoice.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_total=line_total
        )
        db.add(db_line)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    supplier_code: str = None,
    status: InvoiceStatus = None,
    purchase_order_id: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Invoice).options(joinedload(Invoice.lines))
    
    if supplier_code:
        query = query.filter(Invoice.supplier_code == supplier_code)
    if status:
        query = query.filter(Invoice.status == status)
    if purchase_order_id:
        query = query.filter(Invoice.purchase_order_id == purchase_order_id)
    
    invoices = query.offset(skip).limit(limit).all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).options(
        joinedload(Invoice.lines)
    ).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    update_data = invoice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found"
        )
    
    db.delete(invoice)
    db.commit()
    return None
