// src/api/schemas/document.py
"""Document-related schemas."""
import decimal
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models.document import DocumentStatus, DocumentType


class DocumentLineCreate(BaseModel):
    """Schema for creating a document line."""

    line_number: int = Field(..., ge=1, description="Line number")
    external_line_reference: str | None = Field(default=None, description="External reference")
    item_code: str = Field(..., min_length=1, max_length=50, description="Item code")
    item_description: str | None = Field(default=None, max_length=500, description="Item description")
    quantity: decimal.Decimal = Field(..., gt=0, description="Quantity")
    unit_of_measure: str | None = Field(default=None, max_length=20, description="Unit of measure")
    unit_price: decimal.Decimal = Field(..., ge=0, description="Unit price")
    tax_rate: decimal.Decimal = Field(default=decimal.Decimal("0"), ge=0, le=1, description="Tax rate")
    linked_po_line_id: str | None = Field(default=None, description="Linked PO line ID")

    @model_validator(mode="after")
    def calculate_line_amount(self) -> "DocumentLineCreate":
        """Calculate line amount from quantity and unit price."""
        self.line_amount = self.quantity * self.unit_price
        self.tax_amount = self.line_amount * self.tax_rate
        return self

    line_amount: decimal.Decimal = Field(default=decimal.Decimal("0"), description="Line amount (calculated)")
    tax_amount: decimal.Decimal = Field(default=decimal.Decimal("0"), description="Tax amount (calculated)")


class DocumentLineResponse(BaseModel):
    """Schema for document line response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Line ID")
    line_number: int = Field(..., description="Line number")
    external_line_reference: str | None = Field(default=None, description="External reference")
    item_code: str = Field(..., description="Item code")
    item_description: str | None = Field(default=None, description="Item description")
    quantity: decimal.Decimal = Field(..., description="Quantity")
    unit_of_measure: str | None = Field(default=None, description="Unit of measure")
    unit_price: decimal.Decimal = Field(..., description="Unit price")
    line_amount: decimal.Decimal = Field(..., description="Line amount")
    tax_rate: decimal.Decimal = Field(..., description="Tax rate")
    tax_amount: decimal.Decimal = Field(..., description="Tax amount")
    is_matched: bool = Field(..., description="Is line matched")
    matched_quantity: decimal.Decimal = Field(..., description="Matched quantity")
    linked_po_line_id: str | None = Field(default=None, description="Linked PO line ID")


class DocumentCreate(BaseModel):
    """Schema for creating a document."""

    document_number: str = Field(..., min_length=1, max_length=100, description="Document number")
    document_type: DocumentType = Field(..., description="Document type")
    supplier_code: str = Field(..., min_length=1, max_length=50, description="Supplier code")
    supplier_name: str | None = Field(default=None, max_length=255, description="Supplier name")
    supplier_reference: str | None = Field(default=None, max_length=100, description="Supplier reference")
    document_date: date = Field(..., description="Document date")
    due_date: date | None = Field(default=None, description="Due date")
    delivery_date: date | None = Field(default=None, description="Delivery date")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    notes: str | None = Field(default=None, description="Notes")
    metadata_json: dict | None = Field(default=None, description="Additional metadata")
    lines: list[DocumentLineCreate] = Field(default_factory=list, description="Document lines")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        return v.upper()

    @model_validator(mode="after")
    def calculate_totals(self) -> "DocumentCreate":
        """Calculate document totals from lines."""
        subtotal = sum(line.line_amount for line in self.lines)
        tax_amount = sum(line.tax_amount for line in self.lines)
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total_amount = subtotal + tax_amount
        return self

    subtotal: decimal.Decimal = Field(default=decimal.Decimal("0"), description="Subtotal (calculated)")
    tax_amount: decimal.Decimal = Field(default=decimal.Decimal("0"), description="Tax amount (calculated)")
    total_amount: decimal.Decimal = Field(default=decimal.Decimal("0"), description="Total amount (calculated)")


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    document_number: str | None = Field(default=None, max_length=100, description="Document number")
    supplier_code: str | None = Field(default=None, max_length=50, description="Supplier code")
    supplier_name: str | None = Field(default=None, max_length=255, description="Supplier name")
    supplier_reference: str | None = Field(default=None, max_length=100, description="Supplier reference")
    document_date: date | None = Field(default=None, description="Document date")
    due_date: date | None = Field(default=None, description="Due date")
    delivery_date: date | None = Field(default=None, description="Delivery date")
    currency: str | None = Field(default=None, min_length=3, max_length=3, description="Currency code")
    status: DocumentStatus | None = Field(default=None, description="Document status")
    notes: str | None = Field(default=None, description="Notes")
    metadata_json: dict | None = Field(default=None, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Schema for document response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Document ID")
    document_number: str = Field(..., description="Document number")
    document_type: DocumentType = Field(..., description="Document type")
    status: DocumentStatus = Field(..., description="Document status")
    supplier_code: str = Field(..., description="Supplier code")
    supplier_name: str | None = Field(default=None, description="Supplier name")
    supplier_reference: str | None = Field(default=None, description="Supplier reference")
    document_date: date = Field(..., description="Document date")
    due_date: date | None = Field(default=None, description="Due date")
    delivery_date: date | None = Field(default=None, description="Delivery date")
    subtotal: decimal.Decimal = Field(..., description="Subtotal")
    tax_amount: decimal.Decimal = Field(..., description="Tax amount")
    total_amount: decimal.Decimal = Field(..., description="Total amount")
    currency: str = Field(..., description="Currency code")
    linked_po_id: str | None = Field(default=None, description="Linked PO ID")
    is_fully_matched: bool = Field(..., description="Is fully matched")
    matched_amount: decimal.Decimal = Field(..., description="Matched amount")
    remaining_balance: decimal.Decimal = Field(..., description="Remaining balance")
    notes: str | None = Field(default=None, description="Notes")
    metadata_json: dict | None = Field(default=None, description="Metadata")
    lines: list[DocumentLineResponse] = Field(default_factory=list, description="Document lines")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentListResponse(BaseModel):
    """Schema for document list response (without lines for performance)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Document ID")
    document_number: str = Field(..., description="Document number")
    document_type: DocumentType = Field(..., description="Document type")
    status: DocumentStatus = Field(..., description="Document status")
    supplier_code: str = Field(..., description="Supplier code")
    supplier_name: str | None = Field(default=None, description="Supplier name")
    document_date: date = Field(..., description="Document date")
    total_amount: decimal.Decimal = Field(..., description="Total amount")
    currency: str = Field(..., description="Currency code")
    is_fully_matched: bool = Field(..., description="Is fully matched")
    remaining_balance: decimal.Decimal = Field(..., description="Remaining balance")
    created_at: datetime = Field(..., description="Creation timestamp")
