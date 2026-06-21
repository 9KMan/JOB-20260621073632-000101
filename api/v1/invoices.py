// api/v1/invoices.py
"""Invoice API endpoints.

Handles invoice ingestion, retrieval, and status management.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.enums import InvoiceStatus, MatchingStatus
from services.balances import BalanceService
from api.schemas import BaseSchema, PaginatedResponse, PaginationParams

router = APIRouter()


# Request/Response Models
class InvoiceLineCreate(BaseModel):
    """Schema for creating an invoice line."""

    line_number: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    product_sku: str | None = None
    product_name: str | None = None


class InvoiceLineResponse(BaseSchema):
    """Schema for invoice line response."""

    id: UUID
    invoice_id: UUID
    line_number: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    matched_quantity: Decimal
    is_matched: bool
    match_confidence: float | None
    product_sku: str | None
    product_name: str | None


class InvoiceCreate(BaseSchema):
    """Schema for creating an invoice."""

    vendor_id: str | None = None
    vendor_number: str
    vendor_name: str
    invoice_number: str
    invoice_date: datetime
    due_date: datetime | None = None
    received_date: datetime | None = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    currency_code: str = "USD"
    payment_terms: str | None = None
    description: str | None = None
    lines: list[InvoiceLineCreate]

    @field_validator("received_date", mode="before")
    @classmethod
    def set_received_date(cls, v: datetime | None) -> datetime:
        return v or datetime.utcnow()


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    status: InvoiceStatus | None = None
    is_approved: bool | None = None
    approved_by: str | None = None
    payment_terms: str | None = None
    description: str | None = None


class InvoiceResponse(BaseSchema):
    """Schema for invoice response."""

    id: UUID
    vendor_number: str
    vendor_name: str
    invoice_number: str
    invoice_date: datetime
    due_date: datetime | None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency_code: str
    status: InvoiceStatus
    matching_status: MatchingStatus
    matched_at: datetime | None
    is_approved: bool
    approved_at: datetime | None
    approved_by: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(PaginatedResponse):
    """Paginated list of invoices."""

    items: list[InvoiceResponse]


class InvoiceIngestRequest(BaseModel):
    """Request for bulk invoice ingestion."""

    invoices: list[InvoiceCreate]
    validate_only: bool = False
    skip_duplicates: bool = True


class InvoiceIngestResponse(BaseModel):
    """Response for bulk invoice ingestion."""

    ingested_count: int
    skipped_count: int
    error_count: int
    ingested_ids: list[UUID]
    errors: list[dict] = Field(default_factory=list)


# Endpoints
@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceResponse:
    """Create a new invoice.

    Args:
        invoice_data: Invoice creation data.
        db: Database session.

    Returns:
        Created invoice.
    """
    from models.invoice import Invoice, InvoiceLine

    # Create invoice header
    invoice = Invoice(
        vendor_id=invoice_data.vendor_id,
        vendor_number=invoice_data.vendor_number,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        received_date=invoice_data.received_date or datetime.utcnow(),
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency_code=invoice_data.currency_code,
        payment_terms=invoice_data.payment_terms,
        description=invoice_data.description,
        status=InvoiceStatus.PENDING,
        matching_status=MatchingStatus.PENDING,
    )

    db.add(invoice)
    await db.flush()

    # Create invoice lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            product_sku=line_data.product_sku,
            product_name=line_data.product_name,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    vendor_number: str | None = None,
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    pagination: PaginationParams = Depends(),
) -> InvoiceListResponse:
    """List invoices with optional filtering.

    Args:
        db: Database session.
        vendor_number: Filter by vendor number.
        status_filter: Filter by status.
        date_from: Filter by minimum invoice date.
        date_to: Filter by maximum invoice date.
        pagination: Pagination parameters.

    Returns:
        Paginated list of invoices.
    """
    from models.invoice import Invoice

    query = select(Invoice)
    count_query = select(func.count(Invoice.id))

    # Apply filters
    if vendor_number:
        query = query.where(Invoice.vendor_number == vendor_number)
        count_query = count_query.where(Invoice.vendor_number == vendor_number)

    if status_filter:
        query = query.where(Invoice.status == status_filter)
        count_query = count_query.where(Invoice.status == status_filter)

    if date_from:
        query = query.where(Invoice.invoice_date >= date_from)
        count_query = count_query.where(Invoice.invoice_date >= date_from)

    if date_to:
        query = query.where(Invoice.invoice_date <= date_to)
        count_query = count_query.where(Invoice.invoice_date <= date_to)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(pagination.skip).limit(pagination.limit)

    if pagination.order_by:
        order_col = getattr(Invoice, pagination.order_by, Invoice.created_at)
        if pagination.order_dir == "desc":
            order_col = order_col.desc()
        query = query.order_by(order_col)
    else:
        query = query.order_by(Invoice.created_at.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        has_more=(pagination.skip + len(invoices)) < total,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceResponse:
    """Get a single invoice by ID.

    Args:
        invoice_id: Invoice UUID.
        db: Database session.

    Returns:
        Invoice details.

    Raises:
        HTTPException: If invoice not found.
    """
    from models.invoice import Invoice

    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceResponse:
    """Update an invoice.

    Args:
        invoice_id: Invoice UUID.
        update_data: Fields to update.
        db: Database session.

    Returns:
        Updated invoice.

    Raises:
        HTTPException: If invoice not found.
    """
    from models.invoice import Invoice

    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)

    if update_data.is_approved and not invoice.is_approved:
        invoice.approved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.post("/ingest", response_model=InvoiceIngestResponse)
async def ingest_invoices(
    request: InvoiceIngestRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InvoiceIngestResponse:
    """Bulk ingest invoices.

    Args:
        request: Ingestion request with list of invoices.
        db: Database session.

    Returns:
        Ingestion result summary.
    """
    from models.invoice import Invoice, InvoiceLine

    ingested_ids: list[UUID] = []
    skipped_ids: list[UUID] = []
    errors: list[dict] = []

    for idx, invoice_data in enumerate(request.invoices):
        try:
            # Check for duplicates if skip_duplicates is enabled
            if request.skip_duplicates:
                existing = await db.execute(
                    select(Invoice).where(
                        Invoice.vendor_number == invoice_data.vendor_number,
                        Invoice.invoice_number == invoice_data.invoice_number,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped_ids.append(UUID("00000000-0000-0000-0000-000000000000"))
                    continue

            if request.validate_only:
                continue

            # Create invoice
            invoice = Invoice(
                vendor_id=invoice_data.vendor_id,
                vendor_number=invoice_data.vendor_number,
                vendor_name=invoice_data.vendor_name,
                invoice_number=invoice_data.invoice_number,
                invoice_date=invoice_data.invoice_date,
                due_date=invoice_data.due_date,
                received_date=invoice_data.received_date or datetime.utcnow(),
                subtotal=invoice_data.subtotal,
                tax_amount=invoice_data.tax_amount,
                total_amount=invoice_data.total_amount,
                currency_code=invoice_data.currency_code,
                payment_terms=invoice_data.payment_terms,
                description=invoice_data.description,
                status=InvoiceStatus.PENDING,
                matching_status=MatchingStatus.PENDING,
            )

            db.add(invoice)
            await db.flush()

            # Create lines
            for line_data in invoice_data.lines:
                line = InvoiceLine(
                    invoice_id=invoice.id,
                    line_number=line_data.line_number,
                    description=line_data.description,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    line_amount=line_data.line_amount,
                    product_sku=line_data.product_sku,
                    product_name=line_data.product_name,
                )
                db.add(line)

            ingested_ids.append(invoice.id)

        except Exception as e:
            errors.append({
                "index": idx,
                "invoice_number": invoice_data.invoice_number,
                "error": str(e),
            })

    await db.commit()

    return InvoiceIngestResponse(
        ingested_count=len(ingested_ids),
        skipped_count=len(skipped_ids),
        error_count=len(errors),
        ingested_ids=[str(i) for i in ingested_ids],
        errors=errors,
    )
