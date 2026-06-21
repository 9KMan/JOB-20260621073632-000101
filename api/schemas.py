"""Shared Pydantic request/response schemas.

Schemas are deliberately separated from ``models.*`` so the persistence layer
and the HTTP contract can evolve independently.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.enums import (
    DecisionType,
    DocumentStatus,
    ExceptionSeverity,
    ExceptionStatus,
    MatchLayer,
)


# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    db: bool
    version: str


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------


class InvoiceLineIn(BaseModel):
    line_number: int = Field(ge=1)
    sku: Optional[str] = Field(default=None, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    quantity: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    line_total: Decimal = Field(ge=Decimal("0"))
    uom: str = Field(default="EA", max_length=16)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class InvoiceIn(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=64)
    vendor_id: uuid.UUID
    vendor_name: str = Field(min_length=1, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    total_amount: Decimal = Field(ge=Decimal("0"))
    source: str = Field(default="manual", max_length=64)
    is_ocr: bool = False
    notes: Optional[str] = None
    lines: List[InvoiceLineIn] = Field(default_factory=list)


class InvoiceLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line_number: int
    sku: Optional[str]
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    uom: str


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str
    vendor_id: uuid.UUID
    vendor_name: str
    currency: str
    invoice_date: date
    due_date: Optional[date]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: DocumentStatus
    source: str
    is_ocr: bool
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineOut] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    items: List[InvoiceOut]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Purchase Order
# ---------------------------------------------------------------------------


class POLineIn(BaseModel):
    line_number: int = Field(ge=1)
    sku: Optional[str] = Field(default=None, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    ordered_qty: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    line_total: Decimal = Field(ge=Decimal("0"))
    uom: str = Field(default="EA", max_length=16)
    gl_account: Optional[str] = None
    cost_center: Optional[str] = None


class POIn(BaseModel):
    po_number: str = Field(min_length=1, max_length=64)
    vendor_id: uuid.UUID
    vendor_name: str = Field(min_length=1, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    order_date: date
    expected_delivery: Optional[date] = None
    total_amount: Decimal = Field(ge=Decimal("0"))
    buyer: Optional[str] = None
    notes: Optional[str] = None
    lines: List[POLineIn] = Field(default_factory=list)


class POLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line_number: int
    sku: Optional[str]
    description: str
    ordered_qty: Decimal
    received_qty: Decimal
    invoiced_qty: Decimal
    unit_price: Decimal
    line_total: Decimal
    uom: str


class POOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_number: str
    vendor_id: uuid.UUID
    vendor_name: str
    currency: str
    order_date: date
    expected_delivery: Optional[date]
    total_amount: Decimal
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    lines: List[POLineOut] = Field(default_factory=list)


class POListResponse(BaseModel):
    items: List[POOut]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Delivery Note
# ---------------------------------------------------------------------------


class DeliveryNoteLineIn(BaseModel):
    line_number: int = Field(ge=1)
    sku: Optional[str] = Field(default=None, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    received_qty: Decimal = Field(ge=Decimal("0"))
    uom: str = Field(default="EA", max_length=16)
    purchase_order_line_id: Optional[uuid.UUID] = None


class DeliveryNoteIn(BaseModel):
    dn_number: str = Field(min_length=1, max_length=64)
    vendor_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    delivery_date: date
    received_by: Optional[str] = None
    warehouse: Optional[str] = None
    is_ocr: bool = False
    raw_payload: Optional[str] = None
    lines: List[DeliveryNoteLineIn] = Field(default_factory=list)


class DeliveryNoteLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line_number: int
    sku: Optional[str]
    description: str
    received_qty: Decimal
    uom: str
    purchase_order_line_id: Optional[uuid.UUID]


class DeliveryNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dn_number: str
    vendor_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID]
    delivery_date: date
    received_by: Optional[str]
    warehouse: Optional[str]
    status: DocumentStatus
    is_ocr: bool
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineOut] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseModel):
    items: List[DeliveryNoteOut]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Matching & decisions
# ---------------------------------------------------------------------------


class MatchRequest(BaseModel):
    invoice_id: uuid.UUID
    force: bool = Field(default=False, description="Re-run matching even if already processed.")


class LineDecisionOut(BaseModel):
    invoice_line_id: uuid.UUID
    purchase_order_line_id: Optional[uuid.UUID]
    score: float = Field(ge=0.0, le=100.0)
    decision: DecisionType
    layer: MatchLayer
    reasons: List[str] = Field(default_factory=list)


class MatchResultOut(BaseModel):
    invoice_id: uuid.UUID
    overall_score: float
    overall_decision: DecisionType
    decided_at: datetime
    line_decisions: List[LineDecisionOut] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ExceptionOut(BaseModel):
    id: uuid.UUID
    invoice_id: Optional[uuid.UUID]
    purchase_order_id: Optional[uuid.UUID]
    severity: ExceptionSeverity
    status: ExceptionStatus
    summary: str
    detail: Optional[str]
    created_at: datetime
    updated_at: datetime


class ExceptionListResponse(BaseModel):
    items: List[ExceptionOut]
    total: int
    limit: int
    offset: int


class ExceptionResolveIn(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=1024)
    force_post: bool = False


class ExceptionDismissIn(BaseModel):
    reason: str = Field(min_length=1, max_length=1024)


# ---------------------------------------------------------------------------
# Balances & learning
# ---------------------------------------------------------------------------


class BalanceLedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purchase_order_line_id: uuid.UUID
    ordered_qty: Decimal
    received_qty: Decimal
    invoiced_qty: Decimal
    open_qty: Decimal
    ordered_value: Decimal
    invoiced_value: Decimal
    open_value: Decimal
    last_event_at: datetime
    currency: str


class CrossRefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: uuid.UUID
    sku: str
    canonical_description: str
    alias_description: str
    confirmation_count: int
    avg_confidence: float
    is_promoted: bool
