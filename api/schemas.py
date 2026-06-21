# api/schemas.py
"""Shared Pydantic request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for query."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    detail: str | None = None
    code: str | None = None


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    due_date: date | None = None
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    tax_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = None
    source_system: str = Field(default="manual", max_length=50)
    external_reference: str | None = None
    is_credit_memo: bool = False


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    line_amount: Decimal = Field(..., decimal_places=2)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    tax_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""

    lines: list[InvoiceLineBase] = Field(..., min_length=1)


class InvoiceLineResponse(BaseModel):
    """Invoice line response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal | None
    tax_amount: Decimal | None
    po_line_id: str | None
    delivery_note_line_id: str | None
    is_matched: bool
    match_confidence: str | None
    match_score: float | None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    lines: list[InvoiceLineResponse]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    po_number: str = Field(..., min_length=1, max_length=100)
    po_date: date
    delivery_date: date | None = None
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = None
    source_system: str = Field(default="erp", max_length=50)
    department: str | None = None
    cost_center: str | None = None


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    ordered_quantity: Decimal = Field(..., gt=0, decimal_places=3)
    received_quantity: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3)
    invoiced_quantity: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    line_amount: Decimal = Field(..., decimal_places=2)
    tax_rate: Decimal | None = None
    delivery_date: date | None = None
    item_number: str | None = None
    uom: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""

    lines: list[PurchaseOrderLineBase] = Field(..., min_length=1)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    po_id: str
    balance_quantity: Decimal
    invoice_balance: Decimal


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    lines: list[PurchaseOrderLineResponse]
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    dn_number: str = Field(..., min_length=1, max_length=100)
    dn_date: date
    received_date: date | None = None
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = None
    source_system: str = Field(default="erp", max_length=50)
    po_number: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal | None = None
    line_amount: Decimal = Field(..., decimal_places=2)
    po_line_id: str | None = None
    item_number: str | None = None
    uom: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""

    lines: list[DeliveryNoteLineBase] = Field(..., min_length=1)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    dn_id: str
    po_line_id: str | None
    is_invoiced: bool


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    lines: list[DeliveryNoteLineResponse]
    created_at: datetime
    updated_at: datetime


class MatchRequest(BaseModel):
    """Matching request schema."""

    invoice_id: str = Field(..., description="Invoice ID to match")
    force_rematch: bool = Field(
        default=False,
        description="Force rematch even if already matched",
    )


class MatchResultLine(BaseModel):
    """Match result for a single invoice line."""

    line_number: int
    description: str
    invoice_quantity: Decimal
    invoice_unit_price: Decimal
    po_line_id: str | None
    po_description: str | None
    po_quantity: Decimal | None
    po_unit_price: Decimal | None
    quantity_variance_pct: float | None
    price_variance_pct: float | None
    match_score: float
    match_confidence: str
    match_reason: str | None


class MatchResult(BaseModel):
    """Matching result schema."""

    invoice_id: str
    invoice_number: str
    decision: str
    overall_score: float
    auto_approved: bool
    lines: list[MatchResultLine]
    exceptions: list[str] = []
    processing_time_ms: int


class ExceptionResponse(BaseModel):
    """Exception response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    invoice_line_id: str | None
    exception_type: str
    status: str
    description: str
    resolution_notes: str | None
    resolved_by: str | None
    resolved_at: datetime | None
    created_at: datetime


class ExceptionResolve(BaseModel):
    """Exception resolution schema."""

    resolution_notes: str = Field(..., min_length=1, max_length=1000)
    resolved_by: str = Field(..., min_length=1, max_length=100)


class BalanceLedgerResponse(BaseModel):
    """Balance ledger response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    po_line_id: str
    transaction_type: str
    quantity_change: Decimal
    amount_change: Decimal
    running_quantity: Decimal
    running_amount: Decimal
    reference_number: str | None
    description: str | None
    created_at: datetime


class CrossRefResponse(BaseModel):
    """Cross-reference response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_vendor_number: str
    po_vendor_number: str
    vendor_match_score: float
    description_match_score: float
    item_match_score: float
    quantity_match_score: float
    price_match_score: float
    overall_match_score: float
    match_decision: str
    match_count: int
    confirmed_at: str | None
    promotion_weight: float
    created_at: datetime
