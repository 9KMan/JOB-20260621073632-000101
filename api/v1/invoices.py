# api/v1/invoices.py
"""Invoice endpoints for ingestion and CRUD operations."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationMeta,
)
from core.database import get_db
from models.invoice import Invoice, InvoiceLine
from models.enums import InvoiceStatus

router = APIRouter()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice",
    description="Ingest a new invoice with line items.",
)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> Invoice:
    """
    Create a new invoice with line items.
    """
    # Check for duplicate invoice number
    stmt = select(Invoice).where(
        Invoice.invoice_number == invoice_data.invoice_number,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {invoice_data.invoice_number} already exists",
        )

    # Create invoice
    invoice = Invoice(
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        vendor_code=invoice_data.vendor_code,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency=invoice_data.currency,
        source_system=invoice_data.source_system,
        notes=invoice_data.notes,
        status=InvoiceStatus.PENDING,
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
            extended_amount=line_data.extended_amount,
            tax_rate=line_data.tax_rate or 0,
            tax_amount=line_data.tax_amount or 0,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.get(
    "/",
    response_model=PaginatedResponse[InvoiceListResponse],
    summary="List invoices",
    description="Get a paginated list of invoices.",
)
async def list_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    vendor_id: Optional[uuid.UUID] = Query(None, description="Filter by vendor"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List invoices with pagination and optional filters.
    """
    # Build query
    stmt = select(Invoice).where(Invoice.is_deleted == False)

    if vendor_id:
        stmt = stmt.where(Invoice.vendor_id == vendor_id)
    if status:
        stmt = stmt.where(Invoice.status == status)
    if start_date:
        stmt = stmt.where(Invoice.invoice_date >= start_date)
    if end_date:
        stmt = stmt.where(Invoice.invoice_date <= end_date)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Apply pagination
    offset = (page - 1) * per_page
    stmt = stmt.order_by(Invoice.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(stmt)
    invoices = result.scalars().all()

    # Build response
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "data": invoices,
        "meta": PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        ),
    }


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice",
    description="Get a single invoice by ID with line items.",
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Invoice:
    """
    Get invoice by ID with full line item details.
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return invoice


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update invoice",
    description="Update an existing invoice.",
)
async def update_invoice(
    invoice_id: uuid.UUID,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Invoice:
    """
    Update invoice fields.
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Update allowed fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    await db.commit()
    await db.refresh(invoice)

    return invoice


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice",
    description="Soft delete an invoice.",
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete an invoice.
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.soft_delete()
    await db.commit()


@router.post(
    "/{invoice_id}/cancel",
    response_model=InvoiceResponse,
    summary="Cancel invoice",
    description="Cancel an invoice.",
)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Invoice:
    """
    Cancel an invoice.
    """
    stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.is_deleted == False,
    )
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel invoice with status {invoice.status.value}",
        )

    invoice.status = InvoiceStatus.CANCELLED
    await db.commit()
    await db.refresh(invoice)

    return invoice
