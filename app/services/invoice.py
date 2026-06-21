// app/services/invoice.py
"""Invoice service."""
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceLine
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Service for invoice operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_invoice_by_id(self, invoice_id: uuid.UUID) -> Optional[Invoice]:
        """Get an invoice by ID with lines."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(
                and_(Invoice.id == invoice_id, Invoice.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by invoice number."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(
                and_(Invoice.invoice_number == invoice_number, Invoice.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_invoices(
        self,
        skip: int = 0,
        limit: int = 100,
        vendor_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        po_reference: Optional[str] = None,
    ) -> List[Invoice]:
        """Get a list of invoices."""
        query = select(Invoice).options(
            selectinload(Invoice.lines)
        ).where(Invoice.is_deleted == False)
        
        if vendor_id:
            query = query.where(Invoice.vendor_id == vendor_id)
        if status:
            query = query.where(Invoice.status == status)
        if po_reference:
            query = query.where(Invoice.po_reference == po_reference)
        
        query = query.offset(skip).limit(limit).order_by(Invoice.invoice_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_unmatched_invoices(
        self,
        vendor_id: Optional[uuid.UUID] = None,
    ) -> List[Invoice]:
        """Get invoices that haven't been matched yet."""
        query = select(Invoice).options(
            selectinload(Invoice.lines)
        ).where(
            and_(
                Invoice.is_deleted == False,
                Invoice.status == "RECEIVED",
            )
        )
        if vendor_id:
            query = query.where(Invoice.vendor_id == vendor_id)
        query = query.order_by(Invoice.invoice_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice with lines."""
        invoice_dict = invoice_data.model_dump(exclude={"lines"})
        
        # Calculate totals from lines
        lines_data = invoice_dict.pop("lines", [])
        
        # Calculate line totals if not provided
        for line in lines_data:
            if "line_total" not in line or line["line_total"] is None:
                quantity = Decimal(str(line["quantity"]))
                unit_price = Decimal(str(line["unit_price"]))
                tax_rate = Decimal(str(line.get("tax_rate", "0")))
                line["line_total"] = quantity * unit_price * (1 + tax_rate)
        
        # Calculate invoice totals
        subtotal = sum(Decimal(str(line["line_total"])) / (1 + Decimal(str(line.get("tax_rate", "0")))) for line in lines_data)
        tax_amount = sum(
            Decimal(str(line["line_total"])) - (Decimal(str(line["line_total"])) / (1 + Decimal(str(line.get("tax_rate", "0")))))
            for line in lines_data
        )
        
        invoice_dict["subtotal"] = subtotal
        invoice_dict["tax_amount"] = tax_amount
        invoice_dict["total_amount"] = subtotal + tax_amount
        
        # Create invoice
        invoice = Invoice(**invoice_dict)
        self.db.add(invoice)
        await self.db.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data["invoice_id"] = invoice.id
            line = InvoiceLine(**line_data)
            self.db.add(line)
        
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice
    
    async def update_invoice(
        self,
        invoice_id: uuid.UUID,
        invoice_data: InvoiceUpdate,
    ) -> Optional[Invoice]:
        """Update an existing invoice."""
        invoice = await self.get_invoice_by_id(invoice_id)
        if not invoice:
            return None
        
        update_data = invoice_data.model_dump(exclude_unset=True, exclude={"lines"})
        
        # Handle line updates if provided
        if "lines" in update_data and update_data["lines"] is not None:
            # Delete existing lines and create new ones
            for existing_line in invoice.lines:
                await self.db.delete(existing_line)
            
            lines_data = update_data.pop("lines")
            for line_data in lines_data:
                if "line_total" not in line_data or line_data["line_total"] is None:
                    quantity = Decimal(str(line_data["quantity"]))
                    unit_price = Decimal(str(line_data["unit_price"]))
                    tax_rate = Decimal(str(line_data.get("tax_rate", "0")))
                    line_data["line_total"] = quantity * unit_price * (1 + tax_rate)
                line_data["invoice_id"] = invoice.id
                line = InvoiceLine(**line_data)
                self.db.add(line)
        
        # Update invoice fields
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        # Recalculate totals
        await self.db.flush()
        await self.db.refresh(invoice)
        await self._recalculate_totals(invoice)
        
        return invoice
    
    async def _recalculate_totals(self, invoice: Invoice) -> None:
        """Recalculate invoice totals from lines."""
        lines = await self.db.execute(
            select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)
        )
        lines = list(lines.scalars().all())
        
        subtotal = sum(
            line.line_total / (1 + line.tax_rate) for line in lines
        )
        tax_amount = sum(
            line.line_total - (line.line_total / (1 + line.tax_rate))
            for line in lines
        )
        
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal + tax_amount
        await self.db.flush()
    
    async def update_invoice_status(
        self,
        invoice_id: uuid.UUID,
        status: str,
    ) -> Optional[Invoice]:
        """Update invoice status."""
        invoice = await self.get_invoice_by_id(invoice_id)
        if not invoice:
            return None
        invoice.status = status
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice
    
    async def delete_invoice(self, invoice_id: uuid.UUID) -> bool:
        """Soft delete an invoice."""
        invoice = await self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False
        
        invoice.is_deleted = True
        invoice.deleted_at = invoice.updated_at
        await self.db.flush()
        return True
