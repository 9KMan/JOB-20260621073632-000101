// src/services/invoice_service.py
"""Invoice service for business logic."""
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.services.base import BaseService


class InvoiceService(BaseService[Invoice]):
    """Service for Invoice operations."""

    def __init__(self, db: Session):
        """Initialize invoice service."""
        super().__init__(Invoice, db)

    def get_with_lines(self, id: UUID) -> Optional[Invoice]:
        """Get invoice with lines eagerly loaded."""
        stmt = (
            select(Invoice)
            .options(joinedload(Invoice.lines))
            .options(joinedload(Invoice.supplier))
            .where(
                Invoice.id == id,
                Invoice.is_deleted == False,  # noqa: E712
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return self.get_by_field("invoice_number", invoice_number)

    def get_by_supplier_and_number(
        self, supplier_id: UUID, invoice_number: str
    ) -> Optional[Invoice]:
        """Get invoice by supplier and invoice number."""
        stmt = select(Invoice).where(
            Invoice.supplier_id == supplier_id,
            Invoice.invoice_number == invoice_number,
            Invoice.is_deleted == False,  # noqa: E712
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_pending_invoices(self) -> List[Invoice]:
        """Get all pending invoices (not yet matched or approved)."""
        stmt = (
            select(Invoice)
            .options(joinedload(Invoice.lines))
            .options(joinedload(Invoice.supplier))
            .where(
                Invoice.status == InvoiceStatus.RECEIVED,
                Invoice.is_deleted == False,  # noqa: E712
            )
            .order_by(Invoice.invoice_date)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, data: dict) -> Invoice:
        """Create a new invoice with lines."""
        lines_data = data.pop("lines", [])

        # Calculate totals if not provided
        subtotal = Decimal(str(data.get("subtotal", 0)))
        tax_amount = Decimal(str(data.get("tax_amount", 0)))
        total_amount = Decimal(str(data.get("total_amount", 0)))

        if subtotal == 0 and lines_data:
            subtotal = sum(Decimal(str(line.get("line_total", 0))) for line in lines_data)
            tax_amount = sum(Decimal(str(line.get("tax_amount", 0))) for line in lines_data)
            total_amount = subtotal + tax_amount

        invoice_data = {
            **data,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        }

        invoice = Invoice(**invoice_data)
        self.db.add(invoice)
        self.db.flush()

        # Create lines
        for line_data in lines_data:
            line_data["invoice_id"] = invoice.id
            line = InvoiceLine(**line_data)
            self.db.add(line)

        self.db.flush()
        self.db.refresh(invoice)
        return invoice

    def update(self, id: UUID, data: dict) -> Optional[Invoice]:
        """Update an invoice."""
        invoice = self.get(id)
        if invoice:
            lines_data = data.pop("lines", None)

            for field, value in data.items():
                if hasattr(invoice, field) and value is not None:
                    setattr(invoice, field, value)

            if lines_data is not None:
                # Update lines
                for line_data in lines_data:
                    line_id = line_data.pop("id", None)
                    if line_id:
                        line = self.db.get(InvoiceLine, line_id)
                        if line:
                            for field, value in line_data.items():
                                if hasattr(line, field) and value is not None:
                                    setattr(line, field, value)
                    else:
                        line_data["invoice_id"] = invoice.id
                        line = InvoiceLine(**line_data)
                        self.db.add(line)

            self.db.flush()
            self.db.refresh(invoice)
        return invoice

    def update_status(self, id: UUID, status: InvoiceStatus) -> Optional[Invoice]:
        """Update invoice status."""
        return self.update(
            id, {"status": status.value if isinstance(status, InvoiceStatus) else status}
        )

    def get_multi_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Invoice], int]:
        """Get invoices with pagination and filters."""
        stmt = (
            select(Invoice)
            .options(joinedload(Invoice.supplier))
            .options(joinedload(Invoice.lines))
            .where(Invoice.is_deleted == False)  # noqa: E712
        )

        if supplier_id:
            stmt = stmt.where(Invoice.supplier_id == supplier_id)

        if status:
            stmt = stmt.where(Invoice.status == status)

        if search:
            stmt = stmt.where(Invoice.invoice_number.ilike(f"%{search}%"))

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar()

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size).order_by(Invoice.created_at.desc())

        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total
