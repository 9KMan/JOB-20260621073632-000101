// src/app/services/invoice_service.py
"""
Invoice Service
Handles invoice-related business logic.
"""
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceLine
from app.services.base import BaseService


class InvoiceService(BaseService[Invoice]):
    """Service for Invoice operations."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(Invoice, session)
    
    async def get_with_lines(self, invoice_id: UUID) -> Optional[Invoice]:
        """Get invoice with all lines."""
        session = await self._get_session()
        result = await session.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by number."""
        session = await self._get_session()
        result = await session.execute(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()
    
    async def get_unmatched_invoices(self, supplier_id: Optional[UUID] = None) -> List[Invoice]:
        """Get all unmatched/pending invoices."""
        session = await self._get_session()
        query = select(Invoice).options(selectinload(Invoice.lines)).where(
            Invoice.status == "pending"
        )
        
        if supplier_id:
            query = query.where(Invoice.supplier_id == supplier_id)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def create_invoice(self, data: dict) -> Invoice:
        """Create new invoice with lines."""
        session = await self._get_session()
        
        # Extract lines data
        lines_data = data.pop("lines", [])
        
        # Calculate totals
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")
        
        for line in lines_data:
            line_amount = line["quantity"] * line["unit_price"]
            line_tax = line_amount * line.get("tax_rate", Decimal("0"))
            line["line_amount"] = line_amount
            line["tax_amount"] = line_tax
            line["total_amount"] = line_amount + line_tax
            
            subtotal += line_amount
            total_tax += line_tax
        
        data["subtotal"] = subtotal
        data["tax_amount"] = total_tax
        data["total_amount"] = subtotal + total_tax
        data["amount_paid"] = Decimal("0.00")
        
        # Create invoice
        invoice = Invoice(**data)
        session.add(invoice)
        await session.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data["invoice_id"] = invoice.id
            line = InvoiceLine(**line_data)
            session.add(line)
        
        await session.flush()
        await session.refresh(invoice)
        
        return await self.get_with_lines(invoice.id)
    
    async def update_status(self, invoice_id: UUID, status: str) -> Optional[Invoice]:
        """Update invoice status."""
        return await self.update(invoice_id, {"status": status})
    
    async def record_payment(
        self,
        invoice_id: UUID,
        amount: Decimal,
        payment_reference: str
    ) -> Optional[Invoice]:
        """Record payment for an invoice."""
        invoice = await self.get_with_lines(invoice_id)
        if not invoice:
            return None
        
        new_amount_paid = invoice.amount_paid + amount
        
        if new_amount_paid >= invoice.total_amount:
            status = "paid"
        else:
            status = invoice.status
        
        await self.update(invoice_id, {
            "amount_paid": new_amount_paid,
            "payment_reference": payment_reference,
            "status": status,
        })
        
        return await self.get_with_lines(invoice_id)
    
    async def get_statistics(self) -> dict:
        """Get invoice statistics."""
        session = await self._get_session()
        
        total = await session.execute(select(func.count(Invoice.id)))
        pending = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.status == "pending")
        )
        matched = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.status == "matched")
        )
        approved = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.status == "approved")
        )
        paid = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.status == "paid")
        )
        disputed = await session.execute(
            select(func.count(Invoice.id)).where(Invoice.status == "disputed")
        )
        
        return {
            "total": total.scalar_one(),
            "pending": pending.scalar_one(),
            "matched": matched.scalar_one(),
            "approved": approved.scalar_one(),
            "paid": paid.scalar_one(),
            "disputed": disputed.scalar_one(),
        }
