// src/app/services/invoice_service.py
"""
Invoice service.
"""
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceLine
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.services.base_service import BaseService


class InvoiceService(BaseService[Invoice]):
    """Service for Invoice operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Invoice, session)

    async def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return await self.get_by(
            "invoice_number", invoice_number, load_relations=["lines", "supplier"]
        )

    async def get_with_relations(self, id: UUID) -> Optional[Invoice]:
        """Get invoice with all relations loaded."""
        result = await self.session.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.lines),
                selectinload(Invoice.supplier),
            )
            .where(Invoice.id == id)
        )
        return result.scalar_one_or_none()

    async def search_invoices(
        self,
        query: str = None,
        supplier_id: UUID = None,
        status: str = None,
        payment_status: str = None,
        date_from: date = None,
        date_to: date = None,
        po_reference: str = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """Search invoices."""
        stmt = select(Invoice).options(selectinload(Invoice.lines))
        
        if query:
            stmt = stmt.where(Invoice.invoice_number.ilike(f"%{query}%"))
        if supplier_id:
            stmt = stmt.where(Invoice.supplier_id == supplier_id)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if payment_status:
            stmt = stmt.where(Invoice.payment_status == payment_status)
        if date_from:
            stmt = stmt.where(Invoice.invoice_date >= date_from)
        if date_to:
            stmt = stmt.where(Invoice.invoice_date <= date_to)
        if po_reference:
            stmt = stmt.where(Invoice.po_reference == po_reference)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_invoice(self, invoice_in: InvoiceCreate) -> Invoice:
        """Create a new invoice with lines."""
        invoice_data = invoice_in.model_dump(exclude={"lines"})
        
        # Calculate totals from lines if not provided
        lines_data = invoice_data.pop("lines")
        if invoice_in.subtotal is None:
            invoice_data["subtotal"] = sum(
                Decimal(str(line["line_total"])) for line in lines_data
            )
        if invoice_in.tax_amount is None:
            invoice_data["tax_amount"] = Decimal("0.00")
        if invoice_in.total_amount is None:
            invoice_data["total_amount"] = (
                invoice_data["subtotal"] + invoice_data["tax_amount"]
            )
        
        # Create invoice
        invoice = Invoice(**invoice_data)
        self.session.add(invoice)
        await self.session.flush()
        
        # Create lines
        for line_data in lines_data:
            line = InvoiceLine(invoice_id=invoice.id, **line_data)
            self.session.add(line)
        
        await self.session.flush()
        await self.session.refresh(invoice)
        
        return await self.get_with_relations(invoice.id)

    async def update_invoice(
        self, id: UUID, invoice_in: InvoiceUpdate
    ) -> Optional[Invoice]:
        """Update an invoice."""
        update_data = invoice_in.model_dump(exclude_unset=True)
        return await self.update(id, update_data)

    async def update_invoice_status(
        self, id: UUID, status: str
    ) -> Optional[Invoice]:
        """Update invoice status."""
        return await self.update(id, {"status": status})

    async def mark_as_paid(
        self, id: UUID, paid_amount: Decimal = None
    ) -> Optional[Invoice]:
        """Mark invoice as paid."""
        invoice = await self.get_with_relations(id)
        if not invoice:
            return None
        
        if paid_amount is None:
            paid_amount = invoice.total_amount
        
        update_data = {
            "payment_status": "paid",
            "paid_date": datetime.utcnow(),
            "paid_amount": paid_amount,
        }
        
        if paid_amount >= invoice.total_amount:
            update_data["status"] = "paid"
        
        return await self.update(id, update_data)

    async def mark_as_matched(self, id: UUID) -> Optional[Invoice]:
        """Mark invoice as matched."""
        return await self.update(id, {"status": "matched"})

    async def mark_as_approved(self, id: UUID) -> Optional[Invoice]:
        """Mark invoice as approved."""
        return await self.update(id, {"status": "approved"})

    async def mark_as_disputed(self, id: UUID, reason: str = None) -> Optional[Invoice]:
        """Mark invoice as disputed."""
        return await self.update(
            id, {"status": "disputed", "notes": reason or "Disputed"}
        )

    async def get_unmatched_invoices(
        self,
        supplier_id: UUID = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """Get invoices that haven't been matched."""
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.status == "pending")
        )
        if supplier_id:
            stmt = stmt.where(Invoice.supplier_id == supplier_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_invoices_for_review(
        self, skip: int = 0, limit: int = 100
    ) -> List[Invoice]:
        """Get all pending invoices that need review."""
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.lines), selectinload(Invoice.supplier))
            .where(Invoice.status == "pending")
            .order_by(Invoice.invoice_date.desc())
        )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
