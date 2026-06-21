// src/schemas/schemas.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
import uuid


# ============ Base Schemas ============

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: datetime


# ============ Supplier Schemas ============

class SupplierBase(BaseSchema):
    """Base supplier schema."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    pass


class SupplierUpdate(BaseSchema):
    """Schema for updating a supplier."""
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase, TimestampMixin):
    """Schema for supplier response."""
    id: UUID


# ============ Line Item Schemas ============

class LineItemBase(BaseSchema):
    """Base line item schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = Field(default=0, ge=0, le=1)
    uom: str = Field(default="EA", max_length=20)


class PurchaseOrderLineCreate(LineItemBase):
    """Schema for creating PO line."""
    pass


class PurchaseOrderLineResponse(LineItemBase, TimestampMixin):
    """Schema for PO line response."""
    id: UUID
    po_id: UUID
    line_amount: float
    tax_amount: float


class InvoiceLineCreate(LineItemBase):
    """Schema for creating invoice line."""
    pass


class InvoiceLineResponse(LineItemBase, TimestampMixin):
    """Schema for invoice line response."""
    id: UUID
    invoice_id: UUID
    line_amount: float
    tax_amount: float


class DeliveryNoteLineCreate(BaseSchema):
    """Schema for creating DN line."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity_delivered: float = Field(..., ge=0)
    quantity_accepted: float = Field(..., ge=0)
    quantity_rejected: float = Field(default=0, ge=0)
    unit_price: float = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)


class DeliveryNoteLineResponse(DeliveryNoteLineCreate, TimestampMixin):
    """Schema for DN line response."""
    id: UUID
    dn_id: UUID
    line_amount: float


# ============ Purchase Order Schemas ============

class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    po_number: str = Field(..., max_length=100)
    supplier_id: UUID
    order_date: datetime
    expected_delivery_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    expected_delivery_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_closed: Optional[bool] = None


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin):
    """Schema for PO response."""
    id: UUID
    total_amount: float
    status: str
    is_closed: bool
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list response."""
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    size: int


# ============ Invoice Schemas ============

class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    invoice_number: str = Field(..., max_length=100)
    supplier_id: UUID
    po_reference: Optional[str] = Field(None, max_length=100)
    invoice_date: datetime
    due_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Schema for invoice response."""
    id: UUID
    total_amount: float
    tax_amount: float
    net_amount: float
    status: str
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list response."""
    items: List[InvoiceResponse]
    total: int
    page: int
    size: int


# ============ Delivery Note Schemas ============

class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    dn_number: str = Field(..., max_length=100)
    supplier_id: UUID
    po_reference: Optional[str] = Field(None, max_length=100)
    delivery_date: datetime
    received_by: Optional[str] = Field(None, max_length=255)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a DN."""
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin):
    """Schema for DN response."""
    id: UUID
    total_amount: float
    status: str
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseSchema):
    """Schema for DN list response."""
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    size: int


# ============ Match Schemas ============

class MatchRecordBase(BaseSchema):
    """Base match record schema."""
    match_type: str
    line_level_score: float = Field(..., ge=0, le=1)
    amount_score: float = Field(..., ge=0, le=1)
    date_score: float = Field(..., ge=0, le=1)
    total_score: float = Field(..., ge=0, le=1)


class MatchRecordResponse(MatchRecordBase, TimestampMixin):
    """Schema for match record response."""
    id: UUID
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    status: str
    po_amount: Optional[float] = None
    invoice_amount: Optional[float] = None
    dn_amount: Optional[float] = None
    variance_amount: Optional[float] = None
    matched_lines: Optional[dict] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    requires_review: bool
    review_notes: Optional[str] = None


class MatchRequest(BaseSchema):
    """Schema for requesting a match."""
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    match_type: str


class MatchDecision(BaseSchema):
    """Schema for match decision."""
    match_id: UUID
    decision: str = Field(..., pattern="^(approve|reject|dispute)$")
    reason: Optional[str] = None
    reviewer_id: Optional[str] = None


class MatchResult(BaseSchema):
    """Schema for match result summary."""
    match_record: MatchRecordResponse
    auto_action: str
    requires_human_review: bool
    balance_summary: dict


# ============ Balance Schemas ============

class BalanceRecordResponse(BaseSchema):
    """Schema for balance record response."""
    id: UUID
    match_record_id: UUID
    document_type: str
    document_id: UUID
    original_amount: float
    matched_amount: float
    balance_amount: float
    is_resolved: bool
    resolved_by_match_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


# ============ Auth Schemas ============

class Token(BaseSchema):
    """Token schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    """Token data schema."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserBase(BaseSchema):
    """Base user schema."""
    email: str
    username: str
    full_name: Optional[str] = None
    role: str = "reviewer"
    approval_limit: float = 0


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    approval_limit: Optional[float] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response."""
    id: UUID
    is_active: bool
    is_superuser: bool


# ============ API Response Schemas ============

class APIResponse(BaseSchema):
    """Generic API response."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[dict] = None


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseSchema):
    """Error response schema."""
    error: str
    message: str
    details: Optional[dict] = None
