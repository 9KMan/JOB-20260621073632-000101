// api/schemas.py
"""Shared Pydantic request/response schemas used across all API endpoints."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Generic type helpers ────────────────────────────────────────────────────────

T = TypeVar("T")


class APIMessage(BaseModel):
    """Simple string-message response for non-data endpoints."""

    message: str
    detail: str | None = None


class APIListResponse(BaseModel, Generic[T]):
    """Paginated list response wrapper."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, default=50)
    pages: int = Field(ge=0)


class ErrorDetail(BaseModel):
    """Structured error detail."""

    field: str | None = None
    message: str


class APIErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    errors: list[ErrorDetail] = Field(default_factory=list)
    request_id: str | None = None


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str | None = None
    version: str | None = None
    database: str = "unknown"


# ── Invoice Schemas ────────────────────────────────────────────────────────────

class InvoiceLineCreate(BaseModel):
    line_number: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=500)
    sku: str | None = Field(None, max_length=100)
    quantity: Annotated[Decimal, Field(gt=0, decimal_places=4)]
    unit_price: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    line_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    tax_rate: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4)] = Decimal("0.0000")
    po_line_id: UUID | None = None

    model_config = ConfigDict(extra="allow")


class InvoiceLineResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    line_number: str
    description: str | None
    sku: str | None
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal
    po_line_id: UUID | None
    matched_qty: Decimal
    match_confidence: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    vendor_number: str = Field(..., max_length=50)
    vendor_name: str | None = Field(None, max_length=255)
    invoice_number: str = Field(..., max_length=100)
    invoice_date: date
    due_date: date | None = None
    total_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    currency: str = Field(default="USD", max_length=3)
    tax_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)] = Decimal("0.0000")
    notes: str | None = None
    po_reference_id: UUID | None = None
    external_reference: str | None = Field(None, max_length=255)
    lines: list[InvoiceLineCreate] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @field_validator("invoice_number")
    @classmethod
    def strip_invoice_number(cls, v: str) -> str:
        return v.strip()


class InvoiceUpdateStatus(BaseModel):
    status: str = Field(..., description="New status value")
    notes: str | None = None


class InvoiceResponse(BaseModel):
    id: UUID
    vendor_number: str
    vendor_name: str | None
    invoice_number: str
    invoice_date: date
    due_date: date | None
    total_amount: Decimal
    currency: str
    tax_amount: Decimal
    notes: str | None
    po_reference_id: UUID | None
    external_reference: str | None
    status: str
    match_score: float | None
    match_decision: str | None
    match_decision_at: datetime | None
    match_decision_by: str | None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListItem(BaseModel):
    id: UUID
    vendor_number: str
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    match_score: float | None
    match_decision: str | None
    po_reference_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Purchase Order Schemas ──────────────────────────────────────────────────────

class POLineCreate(BaseModel):
    line_number: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=500)
    sku: str | None = Field(None, max_length=100)
    quantity: Annotated[Decimal, Field(gt=0, decimal_places=4)]
    unit_price: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    line_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    tax_rate: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4)] = Decimal("0.0000")

    model_config = ConfigDict(extra="allow")


class POLineResponse(BaseModel):
    id: UUID
    po_id: UUID
    line_number: str
    description: str | None
    sku: str | None
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal
    delivered_qty: Decimal
    invoiced_qty: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderCreate(BaseModel):
    po_number: str = Field(..., max_length=100)
    vendor_number: str = Field(..., max_length=50)
    vendor_name: str | None = Field(None, max_length=255)
    po_date: date
    delivery_date: date | None = None
    total_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    external_reference: str | None = Field(None, max_length=255)
    lines: list[POLineCreate] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class PurchaseOrderResponse(BaseModel):
    id: UUID
    po_number: str
    vendor_number: str
    vendor_name: str | None
    po_date: date
    delivery_date: date | None
    total_amount: Decimal
    currency: str
    status: str
    notes: str | None
    external_reference: str | None
    is_anchored: bool
    lines: list[POLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderListItem(BaseModel):
    id: UUID
    po_number: str
    vendor_number: str
    vendor_date: date | None = None
    po_date: date
    total_amount: Decimal
    currency: str
    status: str
    is_anchored: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Delivery Note Schemas ───────────────────────────────────────────────────────

class DNLineCreate(BaseModel):
    line_number: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=500)
    sku: str | None = Field(None, max_length=100)
    quantity: Annotated[Decimal, Field(gt=0, decimal_places=4)]
    unit_price: Annotated[Decimal, Field(ge=0, decimal_places=4)] = Decimal("0.0000")
    line_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)] = Decimal("0.0000")
    po_line_id: UUID | None = None

    model_config = ConfigDict(extra="allow")


class DNLineResponse(BaseModel):
    id: UUID
    dn_id: UUID
    line_number: str
    description: str | None
    sku: str | None
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    po_line_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteCreate(BaseModel):
    dn_number: str = Field(..., max_length=100)
    vendor_number: str = Field(..., max_length=50)
    vendor_name: str | None = Field(None, max_length=255)
    po_reference_id: UUID | None = None
    dn_date: date
    received_date: date | None = None
    total_amount: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    external_reference: str | None = Field(None, max_length=255)
    lines: list[DNLineCreate] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class DeliveryNoteResponse(BaseModel):
    id: UUID
    dn_number: str
    vendor_number: str
    vendor_name: str | None
    po_reference_id: UUID | None
    dn_date: date
    received_date: date | None
    total_amount: Decimal
    currency: str
    status: str
    notes: str | None
    external_reference: str | None
    lines: list[DNLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteListItem(BaseModel):
    id: UUID
    dn_number: str
    vendor_number: str
    dn_date: date
    total_amount: Decimal
    currency: str
    status: str
    po_reference_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Matching Schemas ────────────────────────────────────────────────────────────

class MatchTriggerRequest(BaseModel):
    invoice_id: UUID
    force_rerun: bool = Field(
        default=False, description="Re-run matching even if already decided"
    )


class MatchLineResult(BaseModel):
    invoice_line_id: UUID
    po_line_id: UUID | None
    delivery_note_line_id: UUID | None
    match_score: float
    match_band: str
    price_match: bool
    qty_match: bool
    matched_qty: Decimal
    cross_ref_id: UUID | None


class MatchResult(BaseModel):
    invoice_id: UUID
    decision: str
    overall_score: float
    score_band: str
    line_results: list[MatchLineResult]
    run_at: datetime


class MatchDecisionUpdate(BaseModel):
    invoice_id: UUID
    decision: str = Field(..., description="'approved' | 'rejected'")
    override_score: float | None = Field(None, ge=0, le=100)
    reason: str | None = None


# ── Exception Schemas ───────────────────────────────────────────────────────────

class ExceptionCreate(BaseModel):
    invoice_id: UUID
    exception_type: str
    description: str | None = None
    po_line_id: UUID | None = None
    severity: str = Field(default="medium")


class ExceptionResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    exception_type: str
    description: str | None
    status: str
    severity: str
    resolved_by: str | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveRequest(BaseModel):
    resolution_notes: str | None = None


# ── Balance Ledger Schemas ─────────────────────────────────────────────────────

class BalanceLedgerEntryCreate(BaseModel):
    po_line_id: UUID
    invoice_id: UUID | None = None
    entry_type: str = Field(..., pattern="^(debit|credit|adjustment)$")
    amount: Annotated[Decimal, Field(decimal_places=4)]
    quantity: Annotated[Decimal, Field(decimal_places=4)]
    currency: str = Field(default="USD", max_length=3)
    description: str | None = None


class BalanceLedgerResponse(BaseModel):
    id: UUID
    po_id: UUID
    po_line_id: UUID
    invoice_id: UUID | None
    entry_type: str
    amount: Decimal
    quantity: Decimal
    currency: str
    description: str | None
    running_balance_qty: Decimal
    running_balance_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class POLineBalanceResponse(BaseModel):
    po_line_id: UUID
    po_id: UUID
    po_number: str | None
    line_number: str
    sku: str | None
    ordered_qty: Decimal
    delivered_qty: Decimal
    invoiced_qty: Decimal
    balance_qty: Decimal
    balance_amount: Decimal
    currency: str


# ── Pagination ──────────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=200, default=50)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
