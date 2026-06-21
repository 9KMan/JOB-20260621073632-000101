// src/app/services/invoice_service.py
"""Invoice service."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceSummary,
)


class InvoiceService:
    """Service for Invoice operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice with lines."""
        invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            supplier_id=uuid.UUID(invoice_data.supplier_id),
            supplier_name=invoice_data.supplier_name,
            supplier_code=invoice_data.supplier_code,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            po_reference=invoice_data.po_reference,
            currency=invoice_data.currency,
            status=invoice_data.status or InvoiceStatus.DRAFT.value,
            notes=invoice_data.notes,
        )
        
        self.db.add(invoice)
        await self.db.flush()
        
        for line_data in invoice_data.lines:
            line = InvoiceLine(
                invoice_id=invoice.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                product_name=line_data.product_name,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                tax_code=line_data.tax_code,
                tax_rate=line_data.tax_rate,
                notes=line_data.notes,
            )
            line.line_amount = line_data.quantity * line_data.unit_price * (1 + line_data.tax_rate / 100)
            self.db.add(line)
        
        await self.db.flush()
        await self._recalculate_totals(invoice.id)
        await self.db.refresh(invoice)
        
        return invoice
    
    async def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get an invoice by ID."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.id == uuid.UUID(invoice_id))
        )
        return result.scalar_one_or_none()
    
    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by invoice number."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()
    
    async def list_invoices(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_code: Optional[str] = None,
        status: Optional[str] = None,
        po_reference: Optional[str] = None,
        is_archived: bool = False,
    ) -> tuple[list[Invoice], int]:
        """List invoices with pagination and filters."""
        query = select(Invoice).options(selectinload(Invoice.lines))
        
        if supplier_code:
            query = query.where(Invoice.supplier_code == supplier_code)
        if status:
            query = query.where(Invoice.status == status)
        if po_reference:
            query = query.where(Invoice.po_reference == po_reference)
        if is_archived is not None:
            query = query.where(Invoice.is_archived == is_archived)
        
        count_query = select(func.count(Invoice.id))
        if supplier_code:
            count_query = count_query.where(Invoice.supplier_code == supplier_code)
        if status:
            count_query = count_query.where(Invoice.status == status)
        if po_reference:
            count_query = count_query.where(Invoice.po_reference == po_reference)
        if is_archived is not None:
            count_query = count_query.where(Invoice.is_archived == is_archived)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(Invoice.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        return list(invoices), total
    
    async def update_invoice(
        self,
        invoice_id: str,
        invoice_data: InvoiceUpdate,
    ) -> Optional[Invoice]:
        """Update an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        update_data = invoice_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice
    
    async def delete_invoice(self, invoice_id: str) -> bool:
        """Delete an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return False
        
        await self.db.delete(invoice)
        await self.db.flush()
        return True
    
    async def archive_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Archive an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        invoice.is_archived = True
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice
    
    async def update_status(self, invoice_id: str, status: str) -> Optional[Invoice]:
        """Update invoice status."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        invoice.status = status
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice
    
    async def link_to_po(self, invoice_id: str, po_id: str) -> Optional[Invoice]:
        """Link invoice to purchase order."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        invoice.po_id = uuid.UUID(po_id)
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice
    
    async def get_open_invoices(
        self,
        supplier_code: Optional[str] = None,
    ) -> list[Invoice]:
        """Get all open (unmatched) invoices."""
        query = select(Invoice).options(selectinload(Invoice.lines)).where(
            Invoice.status == InvoiceStatus.RECEIVED.value,
            Invoice.is_archived == False,
        )
        
        if supplier_code:
            query = query.where(Invoice.supplier_code == supplier_code)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_invoice_summary(self, invoice_id: str) -> Optional[InvoiceSummary]:
        """Get invoice summary for matching."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        return InvoiceSummary(
            id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            supplier_code=invoice.supplier_code,
            total_amount=invoice.total_amount,
            currency=invoice.currency,
            status=invoice.status,
            open_amount=invoice.total_amount,
            line_count=len(invoice.lines),
        )
    
    async def _recalculate_totals(self, invoice_id: uuid.UUID) -> None:
        """Recalculate invoice totals from lines."""
        result = await self.db.execute(
            select(
                func.sum(InvoiceLine.line_amount).label("subtotal"),
                func.sum(InvoiceLine.line_amount * InvoiceLine.tax_rate / 100).label("tax"),
            )
            .where(InvoiceLine.invoice_id == invoice_id)
        )
        row = result.one()
        
        subtotal = row.subtotal or Decimal("0.00")
        tax = row.tax or Decimal("0.00")
        
        inv_result = await self.db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = inv_result.scalar_one()
        invoice.subtotal = subtotal
        invoice.tax_amount = tax
        invoice.total_amount = subtotal + tax
        await self.db.flush()
