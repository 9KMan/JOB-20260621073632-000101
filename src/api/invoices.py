// src/api/invoices.py
"""Invoice API routes."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.invoice import Invoice, InvoiceLine
from src.models.user import User
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
)
from src.api.deps import get_current_user
from src.services.balance_service import BalanceService
from src.services.matching_service import MatchingService


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> Invoice:
    """Create a new Invoice and trigger matching."""
    # Check for duplicate invoice number
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice {invoice_data.invoice_number} already exists"
        )
    
    # Create Invoice
    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        po_reference=invoice_data.po_reference,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        status="PENDING"
    )
    
    db.add(invoice)
    await db.flush()
    
    # Create lines
    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            sku=line_data.sku,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.line_total
        )
        db.add(line)
    
    await db.commit()
    await db.refresh(invoice)
    
    # Create initial balance entry
    await BalanceService.create_initial_balance(
        db,
        "invoice",
        invoice.id,
        invoice.total_amount,
        invoice.currency,
        f"Invoice {invoice.invoice_number} created"
    )
    
    # Trigger Layer 1 matching (PO Anchoring)
    matching_service = MatchingService(db)
    await matching_service.layer1_po_anchoring(invoice)
    
    return invoice


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: str | None = None,
    status: str | None = None,
    invoice_number: str | None = None,
    po_reference: str | None = None,
    _: User = Depends(get_current_user)
) -> InvoiceListResponse:
    """List all Invoices with pagination."""
    query = select(Invoice).options(selectinload(Invoice.lines))
    
    # Apply filters
    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
    if status:
        query = query.where(Invoice.status == status)
    if invoice_number:
        query = query.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if po_reference:
        query = query.where(Invoice.po_reference.ilike(f"%{po_reference}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(Invoice)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Invoice.created_at.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return InvoiceListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> Invoice:
    """Get an Invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> Invoice:
    """Update an Invoice."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.post("/{invoice_id}/rematch", response_model=dict)
async def rematch_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> dict:
    """Re-run matching for an invoice."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    matching_service = MatchingService(db)
    result = await matching_service.process_invoice(invoice)
    
    return {"status": "success", "matches": result}


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user)
) -> None:
    """Soft delete an Invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    from datetime import datetime, timezone
    invoice.deleted_at = datetime.now(timezone.utc)
    await db.commit()
