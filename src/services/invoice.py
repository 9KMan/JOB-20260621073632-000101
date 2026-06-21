// src/services/invoice.py
"""Invoice service."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Invoice business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _calculate_line_total(self, line: dict) -> Decimal:
        """Calculate line total including tax."""
        quantity = Decimal(str(line.quantity))
        unit_price = Decimal(str(line.unit_price))
        tax_rate = Decimal(str(line.get("tax_rate", "0")))
        subtotal = quantity * unit_price
        tax = subtotal * tax_rate
        return subtotal + tax
    
    def _calculate_totals(self, lines: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        """Calculate invoice totals."""
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        for line in lines:
            quantity = Decimal(str(line.quantity))
            unit_price = Decimal(str(line.unit_price))
            tax_rate = Decimal(str(line.get("tax_rate", "0")))
            line_subtotal = quantity * unit_price
            line_tax = line_subtotal * tax_rate
            subtotal += line_subtotal
            tax_amount += line_tax
        return subtotal, tax_amount, subtotal + tax_amount
    
    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice."""
        lines_data = [line.model_dump() for line in invoice_data.lines]
        subtotal, tax_amount, total_amount = self._calculate_totals(lines_data)
        
        invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            supplier_id=invoice_data.supplier_id,
            supplier_name=invoice_data.supplier_name,
            supplier_reference=invoice_data.supplier_reference,
            po_reference=invoice_data.po_reference,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            currency=invoice_data.currency,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=invoice_data.notes,
            status=InvoiceStatus.DRAFT,
        )
        self.db.add(invoice)
        await self.db.flush()
        
        for idx, line_data in enumerate(lines_data):
            line_total = self._calculate_line_total(line_data)
            line = InvoiceLine(
                invoice_id=invoice.id,
                line_number=line_data.get("line_number", idx + 1),
                sku=line_data.get("sku"),
                description=line_data["description"],
                quantity=Decimal(str(line_data["quantity"])),
                unit_of_measure=line_data.get("unit_of_measure", "EA"),
                unit_price=Decimal(str(line_data["unit_price"])),
                tax_rate=Decimal(str(line_data.get("tax_rate", "0"))),
                line_total=line_total,
            )
            self.db.add(line)
        
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice
    
    async def get_invoice(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()
    
    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by number."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()
    
    async def get_invoices(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        po_reference: Optional[str] = None,
    ) -> tuple[list[Invoice], int]:
        """Get invoices with optional filters."""
        query = select(Invoice).options(selectinload(Invoice.lines))
        count_query = select(func.count(Invoice.id))
        
        if supplier_id:
            query = query.where(Invoice.supplier_id == supplier_id)
            count_query = count_query.where(Invoice.supplier_id == supplier_id)
        
        if status:
            query = query.where(Invoice.status == status)
            count_query = count_query.where(Invoice.status == status)
        
        if po_reference:
            query = query.where(Invoice.po_reference == po_reference)
            count_query = count_query.where(Invoice.po_reference == po_reference)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(skip).limit(limit).order_by(Invoice.created_at.desc())
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total
    
    async def update_invoice(
        self,
        invoice_id: UUID,
        invoice_data: InvoiceUpdate,
    ) -> Optional[Invoice]:
        """Update an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        
        update_data = invoice_data.model_dump(exclude_unset=True)
        
        if "lines" in update_data:
            lines_data = update_data.pop("lines")
            for line in invoice.lines:
                await self.db.delete(line)
            await self.db.flush()
            
            subtotal, tax_amount, total_amount = self._calculate_totals(lines_data)
            update_data["subtotal"] = subtotal
            update_data["tax_amount"] = tax_amount
            update_data["total_amount"] = total_amount
            
            for idx, line_data in enumerate(lines_data):
                line_total = self._calculate_line_total(line_data)
                line = InvoiceLine(
                    invoice_id=invoice.id,
                    line_number=line_data.get("line_number", idx + 1),
                    sku=line_data.get("sku"),
                    description=line_data["description"],
                    quantity=Decimal(str(line_data["quantity"])),
                    unit_of_measure=line_data.get("unit_of_measure", "EA"),
                    unit_price=Decimal(str(line_data["unit_price"])),
                    tax_rate=Decimal(str(line_data.get("tax_rate", "0"))),
                    line_total=line_total,
                )
                self.db.add(line)
        
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice
    
    async def update_invoice_status(
        self,
        invoice_id: UUID,
        status: InvoiceStatus,
    ) -> Optional[Invoice]:
        """Update invoice status."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None
        invoice.status = status
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice
    
    async def delete_invoice(self, invoice_id: UUID) -> bool:
        """Delete an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return False
        await self.db.delete(invoice)
        await self.db.commit()
        return True
