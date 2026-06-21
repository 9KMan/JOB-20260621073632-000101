# api/v1/invoices.py
"""Invoice endpoints for the AP Automation Engine.

Provides CRUD operations and matching triggers for invoices.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    InvoiceLineResponse,
    PaginatedResponse,
    MessageResponse,
    ErrorResponse,
    PaginationParams,
)
from models import Invoice, InvoiceLine, InvoiceStatus
from services import MatchingService

router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Invoice created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid invoice data"},
        409: {"model": ErrorResponse, "description": "Invoice number already exists"},
    },
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: DbSession,
) -> InvoiceResponse:
    """Create a new invoice with line items.

    Creates an invoice and its associated line items.
    The invoice starts in PENDING status.
    """
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.invoice_number == invoice_data.invoice_number,
                Invoice.deleted_at.is_(None),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice number '{invoice_data.invoice_number}' already exists",
        )

    # Create invoice
    invoice = Invoice(
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        vendor_tax_id=invoice_data.vendor_tax_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency=invoice_data.currency,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        po_reference=invoice_data.po_reference,
        status=InvoiceStatus.PENDING,
    )
    db.add(invoice)
    await db.flush()

    # Create line items
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            description=line_data.description,
            sku=line_data.sku,
            quantity=line_data.quantity,
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            po_line_reference=line_data.po_line_reference,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "",
    response_model=PaginatedResponse[InvoiceResponse],
    responses={
        200: {"description": "List of invoices"},
    },
)
async def list_invoices(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    invoice_date_from: datetime | None = Query(default=None),
    invoice_date_to: datetime | None = Query(default=None),
) -> PaginatedResponse[InvoiceResponse]:
    """List all invoices with optional filtering.

    Supports filtering by vendor, status, and date range.
    Results are paginated and sorted by invoice date descending.
    """
    # Build query
    query = select(Invoice).where(Invoice.deleted_at.is_(None))
    count_query = select(func.count(Invoice.id)).where(Invoice.deleted_at.is_(None))

    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
        count_query = count_query.where(Invoice.vendor_id == vendor_id)

    if status:
        try:
            status_enum = InvoiceStatus(status)
            query = query.where(Invoice.status == status_enum)
            count_query = count_query.where(Invoice.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter

    if invoice_date_from:
        query = query.where(Invoice.invoice_date >= invoice_date_from.date())
        count_query = count_query.where(Invoice.invoice_date >= invoice_date_from.date())

    if invoice_date_to:
        query = query.where(Invoice.invoice_date <= invoice_date_to.date())
        count_query = count_query.where(Invoice.invoice_date <= invoice_date_to.date())

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Invoice.invoice_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    # Convert to response models
    items = [InvoiceResponse.model_validate(inv) for inv in invoices]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        200: {"description": "Invoice details"},
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def get_invoice(
    invoice_id: UUID,
    db: DbSession,
) -> InvoiceResponse:
    """Get a single invoice by ID.

    Returns the invoice with all line items.
    """
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.deleted_at.is_(None),
            )
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return InvoiceResponse.model_validate(invoice)


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    responses={
        200: {"description": "Invoice updated"},
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def update_invoice(
    invoice_id: UUID,
    update_data: InvoiceUpdate,
    db: DbSession,
) -> InvoiceResponse:
    """Update an invoice.

    Allows updating status, notes, and approval information.
    """
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.deleted_at.is_(None),
            )
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "status" and value:
            setattr(invoice, field, InvoiceStatus(value))
        elif field == "approved_at" and value:
            setattr(invoice, field, datetime.utcnow())
        else:
            setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    response_model=MessageResponse,
    responses={
        200: {"description": "Invoice deleted"},
        404: {"model": ErrorResponse, "description": "Invoice not found"},
    },
)
async def delete_invoice(
    invoice_id: UUID,
    db: DbSession,
    deleted_by: str = Query(default="system"),
) -> MessageResponse:
    """Soft delete an invoice.

    The invoice is marked as deleted but not removed from the database.
    """
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.deleted_at.is_(None),
            )
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.deleted_at = datetime.utcnow()
    invoice.deleted_by = deleted_by

    await db.commit()

    return MessageResponse(message=f"Invoice {invoice_id} deleted successfully")


@router.post(
    "/{invoice_id}/match",
    response_model=dict,
    responses={
        200: {"description": "Matching triggered"},
        404: {"model": ErrorResponse, "description": "Invoice not found"},
        422: {"model": ErrorResponse, "description": "Invoice not in valid state for matching"},
    },
)
async def trigger_matching(
    invoice_id: UUID,
    db: DbSession,
    auto_match: bool = Query(default=True),
) -> dict:
    """Trigger the matching engine for an invoice.

    Processes the invoice through the matching cascade:
    1. PO Anchoring (Layer 1)
    2. Line Matching Cascade (Layer 2)
    3. Scoring and Decision
    4. Learning Loop Integration
    """
    result = await db.execute(
        select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.deleted_at.is_(None),
            )
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Validate invoice state
    if invoice.status not in [InvoiceStatus.PENDING, InvoiceStatus.SUBMITTED]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invoice is in '{invoice.status}' state and cannot be matched",
        )

    # Run matching service
    matching_service = MatchingService(db)
    result = await matching_service.process_invoice(invoice, auto_trigger=auto_match)

    return {
        "invoice_id": str(invoice_id),
        "invoice_number": invoice.invoice_number,
        "match_result": result,
    }
