// src/services/invoice_service.py
"""Invoice service."""
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.invoice import Invoice, InvoiceLine
from src.models.enums import DocumentStatus
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Service for Invoice operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice with lines."""
        invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            supplier_id=invoice_data.supplier_id,
            po_reference=invoice_data.po_reference,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            currency=invoice_data.currency,
            payment_terms=invoice_data.payment_terms,
            notes=invoice_data.notes,
            attachment_url=invoice_data.attachment_url,
            status=DocumentStatus.SUBMITTED,
        )
        
        self.db.add(invoice)
        await self.db.flush()  # Get the invoice ID
        
        # Create lines
        for line_data in invoice_data.lines:
            line = InvoiceLine(
                invoice_id=invoice.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                tax_rate=line_data.tax_rate,
            )
            line.calculate_totals()
            self.db.add(line)
        
        await self.db.flush()
        
        # Recalculate totals
        invoice.calculate_totals()
        
        await self.db.commit()
        await self.db.refresh(invoice)
        
        return invoice

    async def get_invoice_by_id(
        self,
        invoice_id: uuid.UUID,
        include_lines: bool = True
    ) -> Optional[Invoice]:
        """Get an invoice by ID."""
        query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.is_deleted == False
        )
        
        if include_lines:
            query = query.options(selectinload(Invoice.lines))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get an invoice by number."""
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.invoice_number == invoice_number,
                Invoice.is_deleted == False
            ).options(selectinload(Invoice.lines))
        )
        return result.scalar_one_or_none()

    async def update_invoice(
        self,
        invoice_id: uuid.UUID,
        invoice_data: InvoiceUpdate
    ) -> Optional[Invoice]:
        """Update an existing invoice."""
        invoice = await self.get_invoice_by_id(invoice_id)
        if not invoice:
            return None
        
        update_data = invoice_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        await self.db.commit()
        await self.db.refresh(invoice)
        
        return invoice

    async def update_invoice_status(
        self,
        invoice_id: uuid.UUID,
        status: DocumentStatus
    ) -> Optional[Invoice]:
        """Update invoice status."""
        invoice = await self.get_invoice_by_id(invoice_id)
        if not invoice:
            return None
        
        invoice.status = status
        await self.db.commit()
        await self.db.refresh(invoice)
        
        return invoice

    async def delete_invoice(self, invoice_id: uuid.UUID) -> bool:
        """Soft delete an invoice."""
        invoice = await self.get_invoice_by_id(invoice_id)
        if not invoice:
            return False
        
        invoice.soft_delete()
        await self.db.commit()
        
        return True

    async def list_invoices(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[uuid.UUID] = None,
        status: Optional[DocumentStatus] = None,
        invoice_number: Optional[str] = None,
        po_reference: Optional[str] = None
    ) -> tuple[list[Invoice], int]:
        """List invoices with pagination and filtering."""
        query = select(Invoice).where(Invoice.is_deleted == False)
        
        if supplier_id:
            query = query.where(Invoice.supplier_id == supplier_id)
        if status:
            query = query.where(Invoice.status == status)
        if invoice_number:
            query = query.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
        if po_reference:
            query = query.where(Invoice.po_reference.ilike(f"%{po_reference}%"))
        
        # Get total count
        count_query = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)
        if supplier_id:
            count_query = count_query.where(Invoice.supplier_id == supplier_id)
        if status:
            count_query = count_query.where(Invoice.status == status)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get paginated results with lines
        query = query.options(
            selectinload(Invoice.lines),
            selectinload(Invoice.supplier)
        ).offset(skip).limit(limit).order_by(Invoice.invoice_date.desc())
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        return list(invoices), total

    async def find_invoices_by_po_reference(
        self,
        po_number: str,
        supplier_id: uuid.UUID
    ) -> list[Invoice]:
        """Find invoices referencing a PO number for a supplier."""
        result = await self.db.execute(
            select(Invoice)
            .where(
                Invoice.po_reference == po_number,
                Invoice.supplier_id == supplier_id,
                Invoice.is_deleted == False
            )
            .options(selectinload(Invoice.lines))
            .order_by(Invoice.invoice_date.desc())
        )
        return list(result.scalars().all())
