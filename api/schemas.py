# api/schemas.py
"""Shared Pydantic schemas for request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Generic type for paginated responses
T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ErrorResponse(BaseResponse):
    """Error response model."""

    error: str
    detail: str | None = None
    code: str | None = None


class PaginatedResponse(BaseResponse, Generic[T]):
    """Generic paginated response model."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: Annotated[int, Field(ge=1, default=1, description="Page number")]
    page_size: Annotated[int, Field(ge=1, le=100, default=20, description="Items per page")]


class InvoiceLineSchema(BaseResponse):
    """Invoice line schema."""

    id: str
    line_number: str
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_amount: Decimal
    po_line_id: str | None = None
    delivery_line_id: str | None = None
    match_status: str
    match_confidence: float | None = None


class InvoiceCreateSchema(BaseModel):
    """Schema for creating an invoice."""

    model_config = ConfigDict(populate_by_name=True)

    invoice_number: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_code: Annotated[str, Field(min_length=1, max_length=50)]
    vendor_name: str
    invoice_date: date
    due_date: date | None = None
    currency: Annotated[str, Field(default="USD", max_length=3)]
    subtotal: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    tax_amount: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    total_amount: Annotated[Decimal, Field(ge=0)]
    source_system: Annotated[str, Field(default="manual", max_length=50)]
    erp_invoice_id: str | None = None
    metadata: dict | None = None
    lines: list["InvoiceLineCreateSchema"] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate and uppercase currency code."""
        return v.upper()


class InvoiceLineCreateSchema(BaseModel):
    """Schema for creating an invoice line."""

    model_config = ConfigDict(populate_by_name=True)

    line_number: Annotated[str, Field(min_length=1, max_length=50)]
    description: str
    quantity: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: Annotated[str, Field(default="EA", max_length=20)]
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_amount: Annotated[Decimal, Field(ge=0)]
    tax_code: str | None = None
    tax_rate: Annotated[Decimal, Field(ge=0, le=1, default=Decimal("0"))


class InvoiceResponseSchema(BaseResponse):
    """Invoice response schema."""

    id: str
    invoice_number: str
    vendor_code: str
    vendor_name: str
    invoice_date: date
    due_date: date | None = None
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    matched_at: datetime | None = None
    match_confidence: float | None = None
    decision_type: str | None = None
    erp_invoice_id: str | None = None
    source_system: str
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineSchema] = Field(default_factory=list)


class InvoiceListSchema(BaseResponse):
    """Invoice list item schema."""

    id: str
    invoice_number: str
    vendor_code: str
    vendor_name: str
    invoice_date: date
    total_amount: Decimal
    status: str
    match_confidence: float | None = None
    created_at: datetime


class POLineSchema(BaseResponse):
    """Purchase order line schema."""

    id: str
    line_number: str
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_amount: Decimal
    delivered_quantity: Decimal
    invoiced_quantity: Decimal
    status: str


class PurchaseOrderCreateSchema(BaseModel):
    """Schema for creating a purchase order."""

    model_config = ConfigDict(populate_by_name=True)

    po_number: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_code: Annotated[str, Field(min_length=1, max_length=50)]
    vendor_name: str
    po_date: date
    delivery_date: date | None = None
    currency: Annotated[str, Field(default="USD", max_length=3)]
    subtotal: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    tax_amount: Annotated[Decimal, Field(ge=0, default=Decimal("0.00"))]
    total_amount: Annotated[Decimal, Field(ge=0)]
    source_system: Annotated[str, Field(default="erp", max_length=50)]
    erp_po_id: str | None = None
    metadata: dict | None = None
    lines: list["POLineCreateSchema"] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate and uppercase currency code."""
        return v.upper()


class POLineCreateSchema(BaseModel):
    """Schema for creating a PO line."""

    model_config = ConfigDict(populate_by_name=True)

    line_number: Annotated[str, Field(min_length=1, max_length=50)]
    description: str
    quantity: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: Annotated[str, Field(default="EA", max_length=20)]
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_amount: Annotated[Decimal, Field(ge=0)]
    tax_code: str | None = None
    tax_rate: Annotated[Decimal, Field(ge=0, le=1, default=Decimal("0"))]


class PurchaseOrderResponseSchema(BaseResponse):
    """Purchase order response schema."""

    id: str
    po_number: str
    vendor_code: str
    vendor_name: str
    po_date: date
    delivery_date: date | None = None
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    erp_po_id: str | None = None
    source_system: str
    created_at: datetime
    updated_at: datetime
    lines: list[POLineSchema] = Field(default_factory=list)


class PurchaseOrderListSchema(BaseResponse):
    """Purchase order list item schema."""

    id: str
    po_number: str
    vendor_code: str
    vendor_name: str
    po_date: date
    total_amount: Decimal
    status: str
    created_at: datetime


class DeliveryNoteCreateSchema(BaseModel):
    """Schema for creating a delivery note."""

    model_config = ConfigDict(populate_by_name=True)

    dn_number: Annotated[str, Field(min_length=1, max_length=100)]
    po_number: str | None = None
    vendor_code: Annotated[str, Field(min_length=1, max_length=50)]
    vendor_name: str
    delivery_date: date
    received_date: date | None = None
    currency: Annotated[str, Field(default="USD", max_length=3)]
    total_amount: Annotated[Decimal, Field(ge=0)]
    source_system: Annotated[str, Field(default="erp", max_length=50)]
    erp_dn_id: str | None = None
    metadata: dict | None = None
    lines: list["DeliveryNoteLineCreateSchema"] = Field(default_factory=list)


class DeliveryNoteLineCreateSchema(BaseModel):
    """Schema for creating a delivery note line."""

    model_config = ConfigDict(populate_by_name=True)

    line_number: Annotated[str, Field(min_length=1, max_length=50)]
    description: str
    quantity: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: Annotated[str, Field(default="EA", max_length=20)]
    unit_price: Annotated[Decimal, Field(ge=0, default=Decimal("0"))]
    line_amount: Annotated[Decimal, Field(ge=0)]
    po_line_id: str | None = None


class DeliveryNoteResponseSchema(BaseResponse):
    """Delivery note response schema."""

    id: str
    dn_number: str
    po_number: str | None = None
    vendor_code: str
    vendor_name: str
    delivery_date: date
    received_date: date | None = None
    currency: str
    total_amount: Decimal
    status: str
    erp_dn_id: str | None = None
    source_system: str
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListSchema(BaseResponse):
    """Delivery note list item schema."""

    id: str
    dn_number: str
    po_number: str | None = None
    vendor_code: str
    vendor_name: str
    delivery_date: date
    total_amount: Decimal
    status: str
    created_at: datetime


class MatchingResultSchema(BaseResponse):
    """Matching result schema."""

    invoice_id: str
    invoice_number: str
    status: str
    decision_type: str
    match_confidence: float
    matched_lines: int
    total_lines: int
    matched_amount: Decimal
    total_amount: Decimal
    exceptions: list["ExceptionSchema"] = Field(default_factory=list)
    processed_at: datetime


class MatchTriggerSchema(BaseModel):
    """Schema for triggering matching."""

    invoice_id: Annotated[str, Field(description="Invoice ID to match")]
    force_rematch: Annotated[bool, Field(default=False, description="Force rematch if already matched")]


class ExceptionSchema(BaseResponse):
    """Exception schema."""

    id: str
    invoice_id: str
    invoice_line_id: str | None = None
    exception_type: str
    reason: str
    status: str
    confidence_impact: float
    details: dict | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class ExceptionResolveSchema(BaseModel):
    """Schema for resolving an exception."""

    resolution: Annotated[str, Field(min_length=1, max_length=500)]
    action_taken: str | None = None
    notes: str | None = None


class ExceptionDismissSchema(BaseModel):
    """Schema for dismissing an exception."""

    reason: Annotated[str, Field(min_length=1, max_length=500)]
    notes: str | None = None


class BalanceLedgerSchema(BaseResponse):
    """Balance ledger response schema."""

    po_line_id: str
    po_quantity: Decimal
    po_unit_price: Decimal
    po_line_amount: Decimal
    delivered_quantity: Decimal
    delivered_amount: Decimal
    invoiced_quantity: Decimal
    invoiced_amount: Decimal
    paid_quantity: Decimal
    paid_amount: Decimal
    open_quantity: Decimal
    open_amount: Decimal
    last_invoice_date: date | None = None
    last_payment_date: date | None = None
    is_balanced: bool
    balance_date: date | None = None


# Update forward references
InvoiceCreateSchema.model_rebuild()
