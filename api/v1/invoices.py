# api/v1/invoices.py
"""Invoice endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedResponse,
    PaginationParams,
    BaseResponse,
    HealthResponse,
)
from core.database import get_db
from models import Invoice, InvoiceLine, InvoiceStatus

router = APIRouter()


@router.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    from core.config import settings
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database="connected",
        timestamp=datetime.utcnow(),
    )


@router.post("", response_model=BaseResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[InvoiceResponse]:
    """
    Create a new invoice.
    
    Ingests an invoice with line items for processing.
    """
    # Check for duplicate invoice number
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice with number '{invoice_data.invoice_number}' already exists",
        )
    
    # Create invoice
    invoice = Invoice(
        vendor_id=invoice_data.vendor_id,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        currency=invoice_data.currency,
        source=invoice_data.source,
        source_reference=invoice_data.source_reference,
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
            unit_of_measure=line_data.unit_of_measure,
            unit_price=line_data.unit_price,
            line_amount=line_data.line_amount,
            tax_rate=line_data.tax_rate,
            tax_amount=line_data.tax_amount,
            po_line_id=line_data.po_line_id,
            dn_line_id=line_data.dn_line_id,
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(invoice)
    
    return BaseResponse(
        success=True,
        message="Invoice created successfully",
        data=InvoiceResponse.model_validate(invoice),
    )


@router.get("", response_model=BaseResponse[PaginatedResponse[InvoiceResponse]])
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_id: str | None = None,
    status: InvoiceStatus | None = None,
    invoice_date_from: datetime | None = None,
    invoice_date_to: datetime | None = None,
) -> BaseResponse[PaginatedResponse[InvoiceResponse]]:
    """
    List invoices with pagination and filtering.
    """
    # Build query
    query = select(Invoice).where(Invoice.is_deleted == False)
    count_query = select(func.count(Invoice.id)).where(Invoice.is_deleted == False)
    
    # Apply filters
    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
        count_query = count_query.where(Invoice.vendor_id == vendor_id)
    
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)
    
    if invoice_date_from:
        query = query.where(Invoice.invoice_date >= invoice_date_from.date())
        count_query = count_query.where(Invoice.invoice_date >= invoice_date_from.date())
    
    if invoice_date_to:
        query = query.where(Invoice.invoice_date <= invoice_date_to.date())
        count_query = count_query.where(Invoice.invoice_date <= invoice_date_to.date())
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    invoices_list = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return BaseResponse(
        success=True,
        data=PaginatedResponse(
            items=[InvoiceResponse.model_validate(inv) for inv in invoices_list],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    )


@router.get("/{invoice_id}", response_model=BaseResponse[InvoiceResponse])
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[InvoiceResponse]:
    """
    Get invoice by ID.
    """
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )
    
    return BaseResponse(
        success=True,
        data=InvoiceResponse.model_validate(invoice),
    )


@router.patch("/{invoice_id}", response_model=BaseResponse[InvoiceResponse])
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BaseResponse[InvoiceResponse]:
    """
    Update invoice fields.
    """
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )
    
    # Update allowed fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(invoice, field, InvoiceStatus(value))
        elif value is not None:
            setattr(invoice, field, value)
    
    await db.commit()
    await db.refresh(invoice)
    
    return BaseResponse(
        success=True,
        message="Invoice updated successfully",
        data=InvoiceResponse.model_validate(invoice),
    )


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Soft delete an invoice.
    """
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )
    
    invoice.soft_delete()
    await db.commit()
