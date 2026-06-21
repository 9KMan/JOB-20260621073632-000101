// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.common import BaseSchema, PaginatedResponse, TimestampMixin, SoftDeleteMixin
from src.schemas.supplier import SupplierSummary


class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., ge=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    notes: Optional[str] = None
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating DN line."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampMixin):
    """Schema for DN line response."""
    id: UUID
    dn_id: UUID


class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    dn_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    issue_date: str  # ISO date string
    received_date: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a DN."""
    supplier_id: Optional[UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    issue_date: Optional[str] = None
    received_date: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin, SoftDeleteMixin):
    """Schema for DN response."""
    id: UUID
    status: str
    supplier: Optional[SupplierSummary] = None
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)
    match_records_count: Optional[int] = 0


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Schema for paginated DN list."""
    pass


class DeliveryNoteSummary(BaseSchema):
    """Lightweight DN summary."""
    id: UUID
    dn_number: str
    status: str
    supplier_name: Optional[str] = None
