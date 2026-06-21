# src/services/invoice_service.py
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.schemas.invoice import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    """Service for Invoice operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Get Invoice by ID with lines."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get Invoice by number."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.invoice_number == invoice_number)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[InvoiceStatus] = None
    ) -> List[Invoice]:
        """Get all Invoices with pagination."""
        query = select(Invoice).options(selectinload(Invoice.lines))

        if status:
            query = query.where(Invoice.status == status)

        result = await self.db.execute(
            query.offset(skip).limit(limit).order_by(Invoice.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_supplier(
        self, supplier_id: str, skip: int = 0, limit: int = 100
    ) -> List[Invoice]:
        """Get Invoices by supplier."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .order_by(Invoice.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_po_reference(
        self, po_reference: str, skip: int = 0, limit: int = 100
    ) -> List[Invoice]:
        """Get Invoices by PO reference."""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.po_reference == po_reference)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unmatched(self, supplier_id: Optional[str] = None) -> List[Invoice]:
        """Get unmatched invoices for matching."""
        query = (
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.status.in_([InvoiceStatus.RECEIVED, InvoiceStatus.DRAFT]))
        )

        if supplier_id:
            query = query.where(Invoice.supplier_id == supplier_id)

        result = await self.db.execute(query.order_by(Invoice.invoice_date))
        return list(result.scalars().all())

    async def create(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new Invoice with lines."""
        # Calculate totals
        subtotal = Decimal("0")
        tax_amount = Decimal("0")

        for line in invoice_data.lines:
            line_amount = line.quantity * line.unit_price
            line_tax = line_amount * line.tax_rate if line.tax_rate else Decimal("0")
            subtotal += line_amount
            tax_amount += line_tax

        total_amount = subtotal + tax_amount

        invoice = Invoice(
            invoice_number=invoice_data.invoice_number,
            supplier_id=invoice_data.supplier_id,
            supplier_name=invoice_data.supplier_name,
            supplier_code=invoice_data.supplier_code,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            po_reference=invoice_data.po_reference,
            currency=invoice_data.currency,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=invoice_data.notes,
            metadata=invoice_data.metadata,
            status=InvoiceStatus.RECEIVED,
        )
        self.db.add(invoice)
        await self.db.flush()

        # Create lines
        for line_data in invoice_data.lines:
            line_amount = line_data.quantity * line_data.unit_price
            line_tax = line_amount * (line_data.tax_rate or Decimal("0"))

            invoice_line = InvoiceLine(
                invoice_id=invoice.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                line_amount=line_amount,
                tax_rate=line_data.tax_rate or Decimal("0"),
                tax_amount=line_tax,
                po_line_reference=line_data.po_line_reference,
                notes=line_data.notes,
            )
            self.db.add(invoice_line)

        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def update(self, invoice_id: str, invoice_data: InvoiceUpdate) -> Optional[Invoice]:
        """Update an existing Invoice."""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return None

        update_data = invoice_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)

        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def update_status(self, invoice_id: str, status: InvoiceStatus) -> Optional[Invoice]:
        """Update Invoice status."""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return None
        invoice.status = status
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def delete(self, invoice_id: str) -> bool:
        """Delete an Invoice."""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return False
        await self.db.delete(invoice)
        await self.db.flush()
        return True
