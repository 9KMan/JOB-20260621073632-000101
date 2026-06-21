# src/services/invoice.py
"""Invoice service."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from src.models.invoice import Invoice, InvoiceLine
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Service for invoice management."""

    def __init__(self, db: Session):
        """Initialize invoice service with database session."""
        self.db = db

    def get_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID with line items."""
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.line_items))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.line_items))
            .filter(Invoice.invoice_number == invoice_number)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        purchase_order_id: Optional[UUID] = None,
    ) -> List[Invoice]:
        """Get all invoices with pagination and filters."""
        query = self.db.query(Invoice).options(joinedload(Invoice.line_items))

        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)
        if status:
            query = query.filter(Invoice.status == status)
        if purchase_order_id:
            query = query.filter(Invoice.purchase_order_id == purchase_order_id)

        return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

    def get_total_count(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        purchase_order_id: Optional[UUID] = None,
    ) -> int:
        """Get total count of invoices with filters."""
        query = self.db.query(Invoice)

        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)
        if status:
            query = query.filter(Invoice.status == status)
        if purchase_order_id:
            query = query.filter(Invoice.purchase_order_id == purchase_order_id)

        return query.count()

    def create(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create new invoice with line items."""
        # Calculate net amount from line items if not provided
        net_amount = invoice_data.net_amount
        if invoice_data.line_items:
            net_amount = sum(
                line.line_amount + line.tax_amount for line in invoice_data.line_items
            )

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
            status=invoice_data.status,
            notes=invoice_data.notes,
            purchase_order_id=invoice_data.purchase_order_id,
        )
        self.db.add(invoice)
        self.db.flush()

        # Add line items
        for line_data in invoice_data.line_items:
            line = InvoiceLine(
                invoice_id=invoice.id,
                line_number=line_data.line_number,
                item_code=line_data.item_code,
                item_description=line_data.item_description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                line_amount=line_data.line_amount,
                tax_amount=line_data.tax_amount,
                uom=line_data.uom,
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(invoice)
        return self.get_by_id(invoice.id)

    def update(
        self,
        invoice_id: UUID,
        invoice_data: InvoiceUpdate,
    ) -> Optional[Invoice]:
        """Update existing invoice."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None

        update_data = invoice_data.model_dump(exclude_unset=True, exclude={"line_items"})

        for field, value in update_data.items():
            setattr(invoice, field, value)

        # Update line items if provided
        if invoice_data.line_items is not None:
            # Remove existing lines
            self.db.query(InvoiceLine).filter(
                InvoiceLine.invoice_id == invoice_id
            ).delete()

            # Add new lines
            for line_data in invoice_data.line_items:
                line = InvoiceLine(
                    invoice_id=invoice_id,
                    line_number=line_data.line_number,
                    item_code=line_data.item_code,
                    item_description=line_data.item_description,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    line_amount=line_data.line_amount,
                    tax_amount=line_data.tax_amount,
                    uom=line_data.uom,
                )
                self.db.add(line)

            # Recalculate totals
            invoice.net_amount = sum(
                line.line_amount + line.tax_amount for line in invoice_data.line_items
            )
            invoice.total_amount = sum(
                line.line_amount for line in invoice_data.line_items
            )
            invoice.tax_amount = sum(
                line.tax_amount for line in invoice_data.line_items
            )

        self.db.commit()
        self.db.refresh(invoice)
        return self.get_by_id(invoice_id)

    def update_status(self, invoice_id: UUID, status: str) -> Optional[Invoice]:
        """Update invoice status."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None

        invoice.status = status
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def delete(self, invoice_id: UUID) -> bool:
        """Delete invoice."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return False

        self.db.delete(invoice)
        self.db.commit()
        return True

    def get_unmatched_invoices(self, supplier_id: Optional[str] = None) -> List[Invoice]:
        """Get invoices that haven't been matched yet."""
        query = (
            self.db.query(Invoice)
            .options(joinedload(Invoice.line_items))
            .filter(Invoice.status == "pending")
        )

        if supplier_id:
            query = query.filter(Invoice.supplier_id == supplier_id)

        return query.all()
