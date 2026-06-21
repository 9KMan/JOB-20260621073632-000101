// src/models/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class MatchStatus(str, Enum):
    """Match status enumeration."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class MatchDecision(str, Enum):
    """Match decision enumeration."""
    AUTO_APPROVE = "AUTO_APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    DISPUTE = "DISPUTE"


# Token schemas
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[str] = None


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Vendor schemas
class VendorBase(BaseModel):
    """Base vendor schema."""
    vendor_code: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None


class VendorCreate(VendorBase):
    """Vendor creation schema."""
    pass


class VendorResponse(VendorBase):
    """Vendor response schema."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Purchase Order schemas
class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""
    line_number: int
    item_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """PO line response schema."""
    id: UUID
    purchase_order_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base PO schema."""
    po_number: str
    vendor_id: UUID
    order_date: datetime
    expected_delivery_date: Optional[datetime] = None
    currency: str = "USD"
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """PO creation schema."""
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderLineWithRelations(PurchaseOrderLineResponse):
    """PO line with relationships."""
    pass


class PurchaseOrderResponse(PurchaseOrderBase):
    """PO response schema."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []
    vendor: Optional[VendorResponse] = None

    class Config:
        from_attributes = True


# Invoice schemas
class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int
    item_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    po_line_id: Optional[UUID] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: UUID
    invoice_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str
    vendor_id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_date: datetime
    due_date: Optional[datetime] = None
    currency: str = "USD"
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: List[InvoiceLineCreate]


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []
    vendor: Optional[VendorResponse] = None
    purchase_order: Optional[PurchaseOrderResponse] = None

    class Config:
        from_attributes = True


# Delivery Note schemas
class DeliveryNoteLineBase(BaseModel):
    """Base DN line schema."""
    line_number: int
    item_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    line_total: Decimal
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """DN line creation schema."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """DN line response schema."""
    id: UUID
    delivery_note_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    """Base DN schema."""
    dn_number: str
    vendor_id: UUID
    purchase_order_id: Optional[UUID] = None
    delivery_date: datetime
    currency: str = "USD"
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """DN creation schema."""
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteResponse(DeliveryNoteBase):
    """DN response schema."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []
    vendor: Optional[VendorResponse] = None
    purchase_order: Optional[PurchaseOrderResponse] = None

    class Config:
        from_attributes = True


# Match Result schemas
class MatchScoreBase(BaseModel):
    """Base match score schema."""
    invoice_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    score: float
    quantity_match_score: float = 0
    price_match_score: float = 0
    description_match_score: float = 0
    quantity_difference: Decimal = Decimal("0")
    price_difference: Decimal = Decimal("0")


class MatchScoreResponse(MatchScoreBase):
    """Match score response schema."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MatchResultCreate(BaseModel):
    """Match result creation schema."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID
    match_type: str
    total_score: float
    line_score: float
    amount_score: float
    date_score: float
    amount_difference: Decimal = Decimal("0")
    quantity_difference: Decimal = Decimal("0")
    notes: Optional[str] = None


class MatchResultResponse(BaseModel):
    """Match result response schema."""
    id: UUID
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID
    match_type: str
    match_status: MatchStatus
    match_decision: Optional[MatchDecision] = None
    total_score: float
    line_score: float
    amount_score: float
    date_score: float
    amount_difference: Decimal
    quantity_difference: Decimal
    notes: Optional[str] = None
    decided_by: Optional[UUID] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    scores: List[MatchScoreResponse] = []
    invoice: Optional[InvoiceResponse] = None
    delivery_note: Optional[DeliveryNoteResponse] = None
    purchase_order: Optional[PurchaseOrderResponse] = None

    class Config:
        from_attributes = True


class MatchDecisionRequest(BaseModel):
    """Request to make a match decision."""
    decision: MatchDecision
    notes: Optional[str] = None


# Balance Ledger schemas
class BalanceLedgerResponse(BaseModel):
    """Balance ledger response schema."""
    id: UUID
    document_type: str
    document_id: UUID
    document_line_id: Optional[UUID] = None
    balance_type: str
    amount: Decimal
    related_document_type: Optional[str] = None
    related_document_id: Optional[UUID] = None
    currency: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Pagination schemas
class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    items: List
    total: int
    page: int
    page_size: int
    pages: int
