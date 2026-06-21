// src/services/invoice_service.py
"""Invoice service."""
import uuid
import decimal
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from src.models.invoice import Invoice, InvoiceLine
from src.models.enums import DocumentStatus
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Service for Invoice operations."""

    @staticmethod
    def calculate_totals(lines: List[dict]) -> tuple[decimal.Decimal, decimal.Decimal]:
        """Calculate subtotal and tax amount from lines."""
        subtotal = decimal.Decimal("0.00")
        tax_amount = decimal.Decimal("0.00")
        
        for line in lines:
            subtotal += decimal.Decimal(str(line.get("line_amount", 0)))
            tax_amount += decimal.Decimal(str(line.get("tax_amount", 0)))
        
        return subtotal, tax_amount

    @staticmethod
    def create_invoice(db: Session, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new Invoice with lines."""
        subtotal = invoice_data.subtotal
        tax_amount = invoice_data.tax_amount
        total_amount = invoice_data.total_amount

        if invoice_data.lines:
            subtotal, tax_amount = InvoiceService.calculate_totals(
                [line.model_dump() for line in invoice_data.lines]
            )
            total_amount = subtotal + tax_amount

        invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            supplier_id=invoice_data.supplier_id,
            supplier_name=invoice_data.supplier_name,
            supplier_reference=invoice_data.supplier_reference,
            purchase_order_id=invoice_data.purchase_order_id,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=invoice_data.amount_paid,
            currency=invoice_data.currency,
            status=invoice_data.status,
            payment_terms=invoice_data.payment_terms,
            notes=invoice_data.notes,
            metadata=invoice_data.metadata,
        )
        db.add(invoice)
        db.flush()

        for line_data in invoice_data.lines:
            line = InvoiceLine(
                invoice_id=invoice.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                line_amount=line_data.line_amount,
                tax_rate=line_data.tax_rate,
                tax_amount=line_data.tax_amount,
                notes=line_data.notes,
            )
            db.add(line)

        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_invoice(db: Session, invoice_id: uuid.UUID) -> Optional[Invoice]:
        """Get an Invoice by ID."""
        return (
            db.query(Invoice)
            .options(joinedload(Invoice.lines))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    @staticmethod
    def get_invoice_by_number(db: Session, invoice_number: str) -> Optional[Invoice]:
        """Get an Invoice by invoice number."""
        return (
            db.query(Invoice)
            .options(joinedload(Invoice.lines))
            .filter(Invoice.invoice_number == invoice_number)
            .first()
        )

    @staticmethod
    def get_invoices(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[DocumentStatus] = None,
        po_id: Optional[uuid.UUID] = None,
    ) -> List[Invoice]:
        """Get a list of Invoices with optional filtering."""
        query = db.query(Invoice).options(joinedload(Invoice.lines))
        
        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)
        if status:
            query = query.filter(Invoice.status == status)
        if po_id:
            query = query.filter(Invoice.purchase_order_id == po_id)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_invoice(
        db: Session,
        invoice: Invoice,
        invoice_data: InvoiceUpdate,
    ) -> Invoice:
        """Update an Invoice."""
        update_data = invoice_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(invoice, key, value)
        
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def delete_invoice(db: Session, invoice: Invoice) -> None:
        """Soft delete an Invoice."""
        invoice.is_deleted = True
        invoice.deleted_at = date.today()
        invoice.status = DocumentStatus.CANCELLED
        db.commit()

    @staticmethod
    def update_status(db: Session, invoice: Invoice, status: DocumentStatus) -> Invoice:
        """Update an Invoice status."""
        invoice.status = status
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_unmatched_invoices(
        db: Session,
        supplier_id: Optional[str] = None,
    ) -> List[Invoice]:
        """Get invoices that haven't been fully matched."""
        query = (
            db.query(Invoice)
            .options(joinedload(Invoice.lines))
            .filter(
                Invoice.is_deleted == False,
                Invoice.status.in_([
                    DocumentStatus.SUBMITTED,
                    DocumentStatus.PARTIALLY_MATCHED,
                ])
            )
        )
        
        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)
        
        return query.all()
