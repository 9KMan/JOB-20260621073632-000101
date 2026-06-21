// src/app/models/invoice.py
"""Invoice and Invoice Line models."""

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.models.base import BaseModel


class Invoice(BaseModel):
    """Invoice header entity."""

    __tablename__ = "invoices"

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    po_reference = Column(String(50), nullable=True, index=True)
    supplier_id = Column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="PENDING")
    payment_status = Column(String(20), nullable=False, default="UNPAID")
    notes = Column(String(1000), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    lines = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"


class InvoiceLine(BaseModel):
    """Invoice line item entity."""

    __tablename__ = "invoice_lines"

    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    uom = Column(String(20), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line_number={self.line_number})>"
