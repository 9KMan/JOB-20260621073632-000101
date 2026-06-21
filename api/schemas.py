# api/schemas.py
"""Shared Pydantic request/response schemas used across API v1 endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.enums import (
    ApprovalDecision,
    DeliveryNoteStatus,
    ExceptionReason,
    ExceptionStatus,
    InvoiceStatus,
    LineMatchStatus,
    MatchConfidence,
    MatchStatus,
    PurchaseOrderStatus,
)


# ── Pagination ────────────────────────────────────────────────────────────────

class PageParams(BaseModel):
    """Common pagination query parameters."""

    page: Annotated[int, Field(ge=1, default=1, description="Page number (1-based)")]
    page_size: Annotated[int, Field(ge=1, le=200, default=50, description="Items per page")]

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Generic paginated list wrapper."""

    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[Any],
        total: int,
        params: PageParams,
    ) -> "PaginatedResponse":
        pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )


# ── Invoice schemas ───────────────────────────────────────────────────────────

class InvoiceLineCreate(BaseModel):
    line_number: Annotated[int, Field(ge=1)]
    description: str
    product_code: str | None = None
    product_name: str | None = None
    quantity: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: str | None = None
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_amount: Annotated[Decimal, Field(ge=0)]

    model_config = ConfigDict(extra="forbid")


class InvoiceLineResponse(InvoiceLineCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID | None = None
    po_line_id: UUID | None = None
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    vendor_code: Annotated[str, Field(min_length=1, max_length=50)]
    vendor_name: Annotated[str, Field(min_length=1, max_length=255)]
    invoice_number: Annotated[str, Field(min_length=1, max_length=100)]
    invoice_date: datetime
    due_date: datetime | None = None
    currency: Annotated[str, Field(default="USD", max_length=3)]
    subtotal: Annotated[Decimal, Field(ge=0)]
    tax_amount: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    total_amount: Annotated[Decimal, Field(ge=0)]
    erp_invoice_id: str | None = None
    raw_payload: dict | None = None
    lines: Annotated[list[InvoiceLineCreate], Field(min_length=1)]

    model_config = ConfigDict(extra="forbid")


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    invoice_number: str
    invoice_date: datetime
    due_date: datetime | None
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    status: InvoiceStatus
    match_score: float | None
    match_confidence: MatchConfidence | None
    approval_decision: ApprovalDecision | None
    decision_at: datetime | None
    erp_invoice_id: str | None
    lines: list[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    invoice_number: str
    invoice_date: datetime
    total_amount: Decimal
    status: InvoiceStatus
    match_score: float | None
    match_confidence: MatchConfidence | None
    created_at: datetime


# ── Purchase Order schemas ─────────────────────────────────────────────────────

class PurchaseOrderLineCreate(BaseModel):
    line_number: Annotated[int, Field(ge=1)]
    description: str
    product_code: str | None = None
    product_name: str | None = None
    quantity_ordered: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: str | None = None
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_amount: Annotated[Decimal, Field(ge=0)]

    model_config = ConfigDict(extra="forbid")


class PurchaseOrderLineResponse(PurchaseOrderLineCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID | None = None
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    latest_dn_line_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(BaseModel):
    vendor_code: Annotated[str, Field(min_length=1, max_length=50)]
    vendor_name: Annotated[str, Field(min_length=1, max_length=255)]
    po_number: Annotated[str, Field(min_length=1, max_length=100)]
    po_date: datetime
    delivery_date: datetime | None = None
    currency: Annotated[str, Field(default="USD", max_length=3)]
    total_amount: Annotated[Decimal, Field(ge=0)]
    erp_po_id: str | None = None
    lines: Annotated[list[PurchaseOrderLineCreate], Field(min_length=1)]

    model_config = ConfigDict(extra="forbid")


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    po_number: str
    po_date: datetime
    delivery_date: datetime | None
    currency: str
    total_amount: Decimal
    status: PurchaseOrderStatus
    erp_po_id: str | None
    lines: list[PurchaseOrderLineResponse] = []
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    po_number: str
    po_date: datetime
    total_amount: Decimal
    status: PurchaseOrderStatus
    created_at: datetime


# ── Delivery Note schemas ──────────────────────────────────────────────────────

class DeliveryNoteLineCreate(BaseModel):
    line_number: Annotated[int, Field(ge=1)]
    description: str
    product_code: str | None = None
    product_name: str | None = None
    quantity_delivered: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: str | None = None

    model_config = ConfigDict(extra="forbid")


class DeliveryNoteLineResponse(DeliveryNoteLineCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dn_id: UUID | None = None
    po_line_id: UUID | None = None
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteCreate(BaseModel):
    vendor_code: Annotated[str, Field(min_length=1, max_length=50)]
    vendor_name: Annotated[str, Field(min_length=1, max_length=255)]
    dn_number: Annotated[str, Field(min_length=1, max_length=100)]
    dn_date: datetime
    receipt_date: datetime | None = None
    source: Annotated[str, Field(default="erp", max_length=20)]
    erp_dn_id: str | None = None
    po_id: UUID | None = None
    lines: Annotated[list[DeliveryNoteLineCreate], Field(min_length=1)]

    model_config = ConfigDict(extra="forbid")


class DeliveryNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    dn_number: str
    dn_date: datetime
    receipt_date: datetime | None
    source: str
    status: DeliveryNoteStatus
    po_id: UUID | None
    lines: list[DeliveryNoteLineResponse] = []
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    dn_number: str
    dn_date: datetime
    status: DeliveryNoteStatus
    created_at: datetime


# ── Matching schemas ──────────────────────────────────────────────────────────

class MatchTriggerRequest(BaseModel):
    invoice_id: UUID
    force_rerun: bool = Field(default=False, description="Re-run matching even if already completed")

    model_config = ConfigDict(extra="forbid")


class MatchDecisionResponse(BaseModel):
    invoice_id: UUID
    status: MatchStatus
    score: float | None
    confidence: MatchConfidence | None
    decision: ApprovalDecision | None
    lines_matched: int
    lines_unmatched: int
    exception_count: int


# ── Exception schemas ──────────────────────────────────────────────────────────

class ExceptionResolveRequest(BaseModel):
    resolution_notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class MatchingExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    po_id: UUID | None
    reason: ExceptionReason
    status: ExceptionStatus
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_notes: str | None
    created_at: datetime


# ── Balance ledger schemas ─────────────────────────────────────────────────────

class BalanceLedgerLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_line_id: UUID
    qty_ordered: Decimal
    qty_delivered: Decimal
    qty_invoiced: Decimal
    qty_pending: Decimal
    amount_ordered: Decimal
    amount_delivered: Decimal
    amount_invoiced: Decimal
    amount_pending: Decimal


class BalanceLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID
    currency: str
    total_open_amount: Decimal
    lines: list[BalanceLedgerLineResponse] = []


# ── CrossRef schemas ───────────────────────────────────────────────────────────

class CrossRefLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_line_id: UUID
    po_line_id: UUID
    product_code_match: bool
    product_name_match: bool
    price_variance_pct: float | None
    qty_variance_pct: float | None
    line_score: float


class CrossRefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    po_id: UUID
    vendor_code: str
    confirmed_score: float
    match_count: int
    last_confirmed_at: datetime
    confidence: MatchConfidence
    lines: list[CrossRefLineResponse] = []


# ── Health / generic ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
