# src/api/v1/schemas.py
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================================
# Base Schemas
# ============================================================================


class LineBase(BaseModel):
    """Base schema for line items."""
    line_number: int
    item_code: str
    item_description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    uom: str = "EA"


# ============================================================================
# User Schemas
# ============================================================================


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_active: bool
    is_admin: bool
    created_at: datetime


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None


# ============================================================================
# Purchase Order Schemas
# ============================================================================


class PurchaseOrderLineCreate(LineBase):
    """Schema for creating PO line."""
    pass


class PurchaseOrderLineResponse(LineBase):
    """Schema for PO line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    purchase_order_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""
    po_number: str
    supplier_id: str
    supplier_name: str
    po_date: datetime
    expected_delivery_date: Optional[datetime] = None
    total_amount: Decimal
    currency: str = "USD"


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""
    supplier_name: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    status: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated PO list response."""
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Invoice Schemas
# ============================================================================


class InvoiceLineCreate(LineBase):
    """Schema for creating Invoice line."""
    po_line_id: Optional[uuid.UUID] = None


class InvoiceLineResponse(LineBase):
    """Schema for Invoice line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    invoice_id: uuid.UUID
    po_line_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""
    invoice_number: str
    supplier_id: str
    supplier_name: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    total_amount: Decimal
    currency: str = "USD"


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""
    supplier_name: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(BaseModel):
    """Schema for paginated Invoice list response."""
    items: List[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Delivery Note Schemas
# ============================================================================


class DeliveryNoteLineCreate(LineBase):
    """Schema for creating Delivery Note line."""
    po_line_id: Optional[uuid.UUID] = None


class DeliveryNoteLineResponse(LineBase):
    """Schema for Delivery Note line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    delivery_note_id: uuid.UUID
    po_line_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""
    dn_number: str
    supplier_id: str
    supplier_name: str
    dn_date: datetime
    received_date: Optional[datetime] = None
    total_amount: Decimal
    currency: str = "USD"


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""
    supplier_name: Optional[str] = None
    received_date: Optional[datetime] = None
    status: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated Delivery Note list response."""
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Matching Schemas
# ============================================================================


class LineMatchDetail(BaseModel):
    """Schema for line-level match details."""
    po_line_id: Optional[uuid.UUID] = None
    invoice_line_id: Optional[uuid.UUID] = None
    dn_line_id: Optional[uuid.UUID] = None
    item_code_match: bool
    quantity_match: bool
    quantity_variance: Optional[Decimal] = None
    amount_match: bool
    amount_variance: Optional[Decimal] = None
    score: Decimal


class MatchResultResponse(BaseModel):
    """Schema for matching result response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    po_id: Optional[uuid.UUID] = None
    dn_id: Optional[uuid.UUID] = None
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    match_status: str
    decision: str
    match_type: str
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None
    line_matching_details: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MatchResultDetailResponse(MatchResultResponse):
    """Schema for detailed matching result with parsed details."""
    line_matches: List[LineMatchDetail] = []


class MatchingResultListResponse(BaseModel):
    """Schema for paginated matching results response."""
    items: List[MatchResultResponse]
    total: int
    page: int
    size: int
    pages: int


class MatchRequest(BaseModel):
    """Schema for manual matching request."""
    invoice_id: Optional[uuid.UUID] = None
    po_id: Optional[uuid.UUID] = None
    dn_id: Optional[uuid.UUID] = None


class MatchConfirmationRequest(BaseModel):
    """Schema for confirming a matching result."""
    matching_result_id: uuid.UUID
    confirmation_status: str = Field(..., pattern="^(CONFIRMED|REJECTED)$")
    comments: Optional[str] = None


class MatchConfirmationResponse(BaseModel):
    """Schema for match confirmation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    matching_result_id: uuid.UUID
    confirmed_by: Optional[uuid.UUID] = None
    confirmation_status: str
    comments: Optional[str] = None
    created_at: datetime


# ============================================================================
# Balance Ledger Schemas
# ============================================================================


class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    reference_type: str
    reference_id: uuid.UUID
    original_amount: Decimal
    matched_amount: Decimal
    remaining_balance: Decimal
    matching_result_id: Optional[uuid.UUID] = None
    is_settled: bool
    settled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Dashboard / Statistics Schemas
# ============================================================================


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_purchase_orders: int
    open_purchase_orders: int
    total_invoices: int
    pending_invoices: int
    total_delivery_notes: int
    pending_delivery_notes: int
    total_matching_results: int
    pending_matches: int
    auto_approved: int
    human_review_required: int
    disputes: int


class MatchScoreBreakdown(BaseModel):
    """Schema for match score breakdown."""
    invoice_po_matches: int
    dn_po_matches: int
    invoice_dn_matches: int
    three_way_matches: int
    average_line_score: Decimal
    average_amount_score: Decimal
    average_date_score: Decimal
    average_total_score: Decimal
