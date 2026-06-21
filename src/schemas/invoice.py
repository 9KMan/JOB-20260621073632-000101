// src/schemas/invoice.py
"""Invoice-related Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, TimestampMixin
from src.schemas.supplier import SupplierSummary


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""

    line_number: int = Field(ge=1)
    sku: Optional[str] = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=4)
    line_total: Decimal = Field(ge=0, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0, decimal_places=4)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating an invoice line."""

    line_number: Optional[int] = Field(default=None, ge=1)
    sku: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, gt=0, decimal_places=3)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    line_total: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)


class InvoiceLineResponse(InvoiceLineBase, TimestampMixin):
    """Schema for invoice line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID


class InvoiceBase(BaseSchema):
    """Base invoice schema."""

    invoice_number: str = Field(min_length=1, max_length=50)
    supplier_id: UUID
    reference_po_number: Optional[str] = Field(default=None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tax_id: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    invoice_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    reference_po_number: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    subtotal: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    amount_paid: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    tax_id: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    supplier: SupplierSummary
    lines: list[InvoiceLineResponse] = Field(default_factory=list)

    @property
    def balance_due(self) -> Decimal:
        """Calculate balance due."""
        return self.total_amount - self.amount_paid


class InvoiceSummary(BaseSchema):
    """Schema for invoice summary in nested responses."""

    id: UUID
    invoice_number: str
    total_amount: Decimal
    status: str
    balance_due: Decimal
