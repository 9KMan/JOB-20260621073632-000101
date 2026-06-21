// src/services/invoice_service.py
"""Invoice service for invoice management."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.models.invoice import Invoice, InvoiceLine
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate
from src.services.base import BaseService
from src.services.audit_service import AuditService


class InvoiceService(BaseService[Invoice]):
    """Service for Invoice management."""

    def __init__(self, db: Session):
        """Initialize invoice service."""
        super().__init__(Invoice, db)
        self.audit_service = AuditService(db)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return (
            self.db.query(Invoice)
            .filter(Invoice.invoice_number == invoice_number)
            .first()
        )

    def get_by_supplier(self, supplier_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get invoices by supplier."""
        return (
            self.db.query(Invoice)
            .filter(Invoice.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_po(self, po_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get invoices linked to a PO."""
        return (
            self.db.query(Invoice)
            .filter(Invoice.po_id == po_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pending_invoices(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all pending invoices."""
        return (
            self.db.query(Invoice)
            .filter(Invoice.status == "pending")
            .options(joinedload(Invoice.lines))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get invoices by status."""
        return (
            self.db.query(Invoice)
            .filter(Invoice.status == status)
            .options(joinedload(Invoice.lines))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_invoice(self, invoice_data: InvoiceCreate, received_by: Optional[str] = None) -> Invoice:
        """Create a new Invoice with lines."""
        # Calculate totals
        subtotal = sum(line.line_total for line in invoice_data.lines)
        tax_amount = sum(line.tax_amount for line in invoice_data.lines)
        total_amount = subtotal + tax_amount

        # Create invoice data
        invoice_dict = invoice_data.model_dump(exclude={"lines"})
        invoice_dict["subtotal"] = subtotal
        invoice_dict["tax_amount"] = tax_amount
        invoice_dict["total_amount"] = total_amount
        invoice_dict["receipt_date"] = datetime.utcnow()
        if received_by:
            invoice_dict["received_by"] = received_by

        # Create invoice with lines
        invoice = Invoice(**invoice_dict)
        self.db.add(invoice)
        self.db.flush()

        # Create lines
        for line_data in invoice_data.lines:
            line_dict = line_data.model_dump()
            line = InvoiceLine(invoice_id=invoice.id, **line_dict)
            self.db.add(line)

        self.db.commit()
        self.db.refresh(invoice)

        # Audit log
        self.audit_service.log_create(invoice, received_by)

        return invoice

    def update_invoice(self, id: str, invoice_data: InvoiceUpdate) -> Optional[Invoice]:
        """Update Invoice."""
        invoice = self.get_by_id(id)
        if not invoice:
            return None

        update_dict = invoice_data.model_dump(exclude_unset=True)
        
        # Audit before update
        self.audit_service.log_update(invoice, update_dict, invoice.received_by)

        return self.update(id, update_dict)

    def match_invoice_to_po(self, invoice_id: str, po_id: str, matched_by: Optional[str] = None) -> Optional[Invoice]:
        """Link invoice to a PO."""
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.po_id = po_id
            self.db.commit()
            self.db.refresh(invoice)
            self.audit_service.log_update(
                invoice, {"po_id": po_id, "matched_by": matched_by}, matched_by
            )
        return invoice

    def update_match_status(self, invoice_id: str, match_score: Decimal, match_status: str) -> Optional[Invoice]:
        """Update invoice match status."""
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.match_score = match_score
            invoice.match_status = match_status
            self.db.commit()
            self.db.refresh(invoice)
        return invoice

    def approve_invoice(self, invoice_id: str, approved_by: str) -> Optional[Invoice]:
        """Approve an invoice."""
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.status = "approved"
            invoice.approved_by = approved_by
            invoice.approved_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(invoice)
            self.audit_service.log_update(
                invoice, {"status": "approved", "approved_by": approved_by}, approved_by
            )
        return invoice

    def reject_invoice(self, invoice_id: str, rejected_by: str, reason: Optional[str] = None) -> Optional[Invoice]:
        """Reject an invoice."""
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.status = "rejected"
            invoice.notes = f"{invoice.notes or ''} | Rejected: {reason}".strip(" |")
            self.db.commit()
            self.db.refresh(invoice)
            self.audit_service.log_update(
                invoice, {"status": "rejected", "reason": reason}, rejected_by
            )
        return invoice

    def mark_as_paid(self, invoice_id: str, payment_reference: str) -> Optional[Invoice]:
        """Mark invoice as paid."""
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.status = "paid"
            invoice.payment_reference = payment_reference
            self.db.commit()
            self.db.refresh(invoice)
        return invoice
