// src/services/invoice_service.py
"""Invoice service."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session, joinedload

from src.models.invoice import Invoice, InvoiceLine
from src.models.enums import DocumentStatus
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate
from src.services.base_service import BaseService


class InvoiceService(BaseService[Invoice, InvoiceCreate, InvoiceUpdate]):
    """Service for Invoice operations."""
    
    def __init__(self, db: Session):
        super().__init__(Invoice, db)
    
    def _calculate_totals(self, lines_data: List[dict]) -> tuple[Decimal, Decimal, Decimal]:
        """Calculate subtotal, tax, and total from lines."""
        subtotal = sum(Decimal(str(line.get('line_amount', 0))) for line in lines_data)
        # Assuming 10% tax rate
        tax_amount = subtotal * Decimal("0.10")
        total = subtotal + tax_amount
        return subtotal, tax_amount, total
    
    def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """
        Create a new Invoice with lines.
        
        Args:
            invoice_data: Invoice creation data
            
        Returns:
            Created Invoice with lines
        """
        # Extract lines data
        lines_data = [line.model_dump() for line in invoice_data.lines]
        
        # Calculate totals if not provided
        if invoice_data.subtotal is None:
            subtotal, tax_amount, total = self._calculate_totals(lines_data)
        else:
            subtotal = invoice_data.subtotal
            tax_amount = invoice_data.tax_amount or Decimal("0.00")
            total = invoice_data.total_amount or subtotal + tax_amount
        
        # Create Invoice
        db_invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            supplier_id=invoice_data.supplier_id,
            po_id=invoice_data.po_id,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            status=DocumentStatus.DRAFT,
            currency=invoice_data.currency,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total,
            notes=invoice_data.notes,
        )
        self.db.add(db_invoice)
        self.db.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data.pop('id', None)
            invoice_line = InvoiceLine(
                invoice_id=db_invoice.id,
                **line_data
            )
            self.db.add(invoice_line)
        
        db_invoice.status = DocumentStatus.OPEN
        self.db.commit()
        self.db.refresh(db_invoice)
        return db_invoice
    
    def get_invoice_with_lines(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get an invoice with its lines eagerly loaded."""
        return self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(
            Invoice.id == invoice_id,
            Invoice.is_deleted == False
        ).first()
    
    def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by its number."""
        return self.get_by(invoice_number=invoice_number)
    
    def get_unmatched_invoices_by_supplier(
        self,
        supplier_id: UUID
    ) -> List[Invoice]:
        """Get all unmatched (open) invoices for a supplier."""
        return self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(
            Invoice.supplier_id == supplier_id,
            Invoice.status.in_([DocumentStatus.OPEN, DocumentStatus.PARTIALLY_MATCHED]),
            Invoice.is_deleted == False
        ).all()
    
    def get_invoices_by_po(self, po_id: UUID) -> List[Invoice]:
        """Get all invoices linked to a specific PO."""
        return self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(
            Invoice.po_id == po_id,
            Invoice.is_deleted == False
        ).all()
    
    def update_invoice(
        self,
        invoice_id: UUID,
        update_data: InvoiceUpdate
    ) -> Optional[Invoice]:
        """Update an Invoice."""
        return self.update(invoice_id, update_data)
    
    def update_invoice_status(
        self,
        invoice_id: UUID,
        status: DocumentStatus
    ) -> Optional[Invoice]:
        """Update invoice status."""
        invoice = self.get(invoice_id)
        if invoice:
            invoice.status = status
            self.db.commit()
            self.db.refresh(invoice)
        return invoice
