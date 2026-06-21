// src/schemas/invoice.py
"""Invoice schemas."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.common import BaseSchema, PaginatedResponse, TimestampMixin, SoftDeleteMixin
from src.schemas.supplier import SupplierSummary


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., ge=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    line_total: Decimal = Field(..., ge=Decimal("0"))
    tax_rate: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""
    pass


class InvoiceLineResponse(InvoiceLineBase, TimestampMixin):
    """Schema for invoice line response."""
    id: UUID
    invoice_id: UUID


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    invoice_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: str  # ISO date string
    due_date: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal = Field(default=Decimal("0"))
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    supplier_id: Optional[UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase, TimestampMixin, SoftDeleteMixin):
    """Schema for invoice response."""
    id: UUID
    status: str
    supplier: Optional[SupplierSummary] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)
    match_records_count: Optional[int] = 0


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Schema for paginated invoice list."""
    pass


class InvoiceSummary(BaseSchema):
    """Lightweight invoice summary."""
    id: UUID
    invoice_number: str
    status: str
    total_amount: Decimal
    supplier_name: Optional[str] = None
