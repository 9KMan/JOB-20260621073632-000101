# api/schemas.py
"""Shared Pydantic request/response models for the API."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class LineItemBase(BaseModel):
    """Base schema for line items."""

    line_number: int = Field(..., ge=1, description="Line item number")
    description: str = Field(..., min_length=1, max_length=500, description="Item description")
    quantity: Decimal = Field(..., ge=0, decimal_places=3, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, decimal_places=4, description="Unit price")
    line_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Line total amount")
    tax_code: str | None = Field(None, max_length=50, description="Tax code")
    notes: str | None = Field(None, description="Line notes")
    po_line_reference: str | None = Field(None, max_length=100, description="PO line reference")


class InvoiceLineCreate(LineItemBase):
    """Schema for creating an invoice line item."""

    pass


class InvoiceLineResponse(LineItemBase):
    """Schema for invoice line item response."""

    id: str = Field(..., description="Line item UUID")
    invoice_id: str = Field(..., description="Parent invoice UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class InvoiceBase(BaseSchema):
    """Base schema for invoice data."""

    vendor_number: str = Field(..., min_length=1, max_length=50, description="Vendor number")
    vendor_name: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    invoice_number: str = Field(..., min_length=1, max_length=100, description="Invoice number")
    invoice_date: datetime = Field(..., description="Invoice date")
    invoice_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Total invoice amount")
    tax_amount: Decimal | None = Field(None, decimal_places=2, description="Tax amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    po_reference: str | None = Field(None, max_length=100, description="PO reference number")
    notes: str | None = Field(None, description="Invoice notes")


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(..., min_length=1, description="Invoice line items")


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    vendor_name: str | None = Field(None, max_length=255, description="Vendor name")
    invoice_amount: Decimal | None = Field(None, ge=0, decimal_places=2, description="Total invoice amount")
    tax_amount: Decimal | None = Field(None, decimal_places=2, description="Tax amount")
    status: str | None = Field(None, description="Invoice status")
    notes: str | None = Field(None, description="Invoice notes")


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: str = Field(..., description="Invoice UUID")
    status: str = Field(..., description="Invoice status")
    approved_at: datetime | None = Field(None, description="Approval timestamp")
    approved_by: str | None = Field(None, description="Approved by user")
    rejected_at: datetime | None = Field(None, description="Rejection timestamp")
    rejected_by: str | None = Field(None, description="Rejected by user")
    rejection_reason: str | None = Field(None, description="Rejection reason")
    is_active: bool = Field(..., description="Is active flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    lines: list[InvoiceLineResponse] = Field(default_factory=list, description="Invoice line items")


class PurchaseOrderLineCreate(LineItemBase):
    """Schema for creating a PO line item."""

    pass


class PurchaseOrderLineResponse(LineItemBase):
    """Schema for PO line item response."""

    id: str = Field(..., description="Line item UUID")
    purchase_order_id: str = Field(..., description="Parent PO UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PurchaseOrderBase(BaseSchema):
    """Base schema for purchase order data."""

    vendor_number: str = Field(..., min_length=1, max_length=50, description="Vendor number")
    vendor_name: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    po_number: str = Field(..., min_length=1, max_length=100, description="PO number")
    po_date: datetime = Field(..., description="PO date")
    delivery_date: datetime | None = Field(None, description="Expected delivery date")
    total_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Total PO amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    notes: str | None = Field(None, description="PO notes")


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[PurchaseOrderLineCreate] = Field(..., min_length=1, description="PO line items")


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    id: str = Field(..., description="PO UUID")
    status: str = Field(..., description="PO status")
    is_active: bool = Field(..., description="Is active flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list, description="PO line items")


class DeliveryNoteLineCreate(LineItemBase):
    """Schema for creating a delivery note line item."""

    pass


class DeliveryNoteLineResponse(LineItemBase):
    """Schema for delivery note line item response."""

    id: str = Field(..., description="Line item UUID")
    delivery_note_id: str = Field(..., description="Parent DN UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DeliveryNoteBase(BaseSchema):
    """Base schema for delivery note data."""

    vendor_number: str = Field(..., min_length=1, max_length=50, description="Vendor number")
    vendor_name: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    dn_number: str = Field(..., min_length=1, max_length=100, description="Delivery note number")
    dn_date: datetime = Field(..., description="Delivery note date")
    delivery_date: datetime = Field(..., description="Actual delivery date")
    po_reference: str | None = Field(None, max_length=100, description="PO reference")
    notes: str | None = Field(None, description="DN notes")


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(..., min_length=1, description="DN line items")


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    id: str = Field(..., description="DN UUID")
    status: str = Field(..., description="DN status")
    is_active: bool = Field(..., description="Is active flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list, description="DN line items")


class MatchTriggerRequest(BaseSchema):
    """Schema for triggering matching engine."""

    invoice_id: str = Field(..., description="Invoice ID to match")
    force_rematch: bool = Field(default=False, description="Force rematch even if already matched")


class MatchScoreDetail(BaseSchema):
    """Schema for individual match score components."""

    component: str = Field(..., description="Score component name")
    score: Decimal = Field(..., ge=0, le=1, description="Component score")
    weight: Decimal = Field(..., ge=0, le=1, description="Component weight")
    weighted_score: Decimal = Field(..., ge=0, le=1, description="Weighted score")


class MatchDecisionResponse(BaseSchema):
    """Schema for matching decision response."""

    invoice_id: str = Field(..., description="Invoice ID")
    decision: str = Field(..., description="Match decision")
    confidence_score: Decimal = Field(..., ge=0, le=1, description="Overall confidence score")
    score_breakdown: list[MatchScoreDetail] = Field(default_factory=list, description="Score components")
    matched_po_id: str | None = Field(None, description="Matched PO ID if found")
    matched_po_number: str | None = Field(None, description="Matched PO number")
    matched_lines: list[dict[str, Any]] = Field(default_factory=list, description="Matched line details")
    exceptions: list[str] = Field(default_factory=list, description="Any exceptions raised")
    match_timestamp: datetime = Field(..., description="Match timestamp")


class ExceptionResponse(BaseSchema):
    """Schema for exception response."""

    id: str = Field(..., description="Exception ID")
    invoice_id: str = Field(..., description="Related invoice ID")
    exception_type: str = Field(..., description="Exception type")
    message: str = Field(..., description="Exception message")
    severity: str = Field(default="medium", description="Exception severity")
    matched_po_id: str | None = Field(None, description="PO that was matched (if any)")
    details: dict[str, Any] | None = Field(None, description="Additional exception details")
    status: str = Field(default="open", description="Exception status")
    created_at: datetime = Field(..., description="Creation timestamp")
    resolved_at: datetime | None = Field(None, description="Resolution timestamp")
    resolved_by: str | None = Field(None, description="Resolved by user")


class ExceptionResolveRequest(BaseSchema):
    """Schema for resolving an exception."""

    resolution: str = Field(..., min_length=1, description="Resolution action taken")
    notes: str | None = Field(None, description="Resolution notes")
    approved_override: bool = Field(default=False, description="Override and approve")


class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger response."""

    id: str = Field(..., description="Balance entry ID")
    purchase_order_id: str = Field(..., description="PO ID")
    purchase_order_number: str = Field(..., description="PO number")
    invoice_id: str = Field(..., description="Invoice ID")
    matched_amount: Decimal = Field(..., description="Amount matched")
    matched_quantity: Decimal = Field(..., description="Quantity matched")
    original_po_amount: Decimal = Field(..., description="Original PO amount")
    original_po_quantity: Decimal = Field(..., description="Original PO quantity")
    remaining_amount: Decimal = Field(..., description="Remaining amount")
    remaining_quantity: Decimal = Field(..., description="Remaining quantity")
    match_date: datetime = Field(..., description="Match date")
    match_type: str = Field(..., description="Match type")
    created_at: datetime = Field(..., description="Creation timestamp")


class CrossRefResponse(BaseSchema):
    """Schema for cross-reference learning entry."""

    id: str = Field(..., description="Cross-ref ID")
    vendor_number: str = Field(..., description="Vendor number")
    match_signature: str = Field(..., description="Match signature")
    confidence_score: Decimal = Field(..., ge=0, le=1, description="Confidence score")
    match_count: int = Field(..., description="Number of matches")
    is_promoted: bool = Field(..., description="Is promoted")
    is_confirmed: bool = Field(..., description="Is confirmed")
    confirmed_at: datetime | None = Field(None, description="Confirmation timestamp")
    confirmed_by: str | None = Field(None, description="Confirmed by")
    last_used_at: datetime | None = Field(None, description="Last used timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Page size")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class ErrorResponse(BaseSchema):
    """Schema for error response."""

    detail: str = Field(..., description="Error detail message")
    code: str | None = Field(None, description="Error code")
    field: str | None = Field(None, description="Field that caused the error")


class HealthResponse(BaseSchema):
    """Schema for health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Check timestamp")
