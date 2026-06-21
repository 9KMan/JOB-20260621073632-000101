// src/api/routes/documents.py
"""Document management routes."""
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db
from app.api.schemas.document import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DocumentStatusEnum,
)
from app.api.schemas.common import PaginatedResponse
from app.models.document import (
    PurchaseOrder,
    POLine,
    Invoice,
    InvoiceLine,
    DeliveryNote,
    DeliveryNoteLine,
    DocumentStatus,
)

router = APIRouter()


# Purchase Order endpoints
@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=201)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new purchase order."""
    # Check for duplicate PO number
    existing = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_data.po_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Purchase order number already exists")

    # Create PO
    po = PurchaseOrder(
        po_number=po_data.po_number,
        supplier_id=po_data.supplier_id,
        supplier_name=po_data.supplier_name,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        total_amount=po_data.total_amount,
        currency=po_data.currency,
        notes=po_data.notes,
        metadata_=po_data.metadata_,
    )
    db.add(po)
    await db.flush()

    # Create lines
    for line_data in po_data.lines:
        line = POLine(
            po_id=po.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.quantity * line_data.unit_price,
            uom=line_data.uom,
        )
        db.add(line)

    await db.commit()
    await db.refresh(po)

    # Load lines
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po.id)
    )
    po = result.scalar_one()

    return _po_to_response(po)


@router.get("/purchase-orders", response_model=PaginatedResponse[PurchaseOrderResponse])
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[DocumentStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all purchase orders with pagination."""
    query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
    count_query = select(func.count(PurchaseOrder.id))

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)
        count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.where(PurchaseOrder.status == DocumentStatus(status.value))
        count_query = count_query.where(PurchaseOrder.status == DocumentStatus(status.value))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(PurchaseOrder.created_at.desc())
    result = await db.execute(query)
    pos = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=[_po_to_response(po) for po in pos],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(po_id: str, db: AsyncSession = Depends(get_db)):
    """Get a purchase order by ID."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return _po_to_response(po)


@router.patch("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: str,
    po_data: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a purchase order."""
    result = await db.execute(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Update fields
    update_data = po_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status":
            value = DocumentStatus(value.value)
        setattr(po, key, value)

    await db.commit()
    await db.refresh(po)
    return _po_to_response(po)


@router.delete("/purchase-orders/{po_id}", status_code=204)
async def delete_purchase_order(po_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a purchase order."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    await db.delete(po)
    await db.commit()


# Invoice endpoints
@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new invoice."""
    existing = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_data.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invoice number already exists")

    invoice = Invoice(
        invoice_number=invoice_data.invoice_number,
        supplier_id=invoice_data.supplier_id,
        supplier_name=invoice_data.supplier_name,
        po_id=invoice_data.po_id,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        total_amount=invoice_data.total_amount,
        tax_amount=invoice_data.tax_amount,
        currency=invoice_data.currency,
        notes=invoice_data.notes,
        metadata_=invoice_data.metadata_,
    )
    db.add(invoice)
    await db.flush()

    for line_data in invoice_data.lines:
        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.quantity * line_data.unit_price,
            uom=line_data.uom,
        )
        db.add(line)

    await db.commit()
    await db.refresh(invoice)

    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    return _invoice_to_response(invoice)


@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[DocumentStatusEnum] = None,
    po_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all invoices with pagination."""
    query = select(Invoice).options(selectinload(Invoice.lines))
    count_query = select(func.count(Invoice.id))

    if supplier_id:
        query = query.where(Invoice.supplier_id == supplier_id)
        count_query = count_query.where(Invoice.supplier_id == supplier_id)
    if status:
        query = query.where(Invoice.status == DocumentStatus(status.value))
        count_query = count_query.where(Invoice.status == DocumentStatus(status.value))
    if po_id:
        query = query.where(Invoice.po_id == po_id)
        count_query = count_query.where(Invoice.po_id == po_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Invoice.created_at.desc())
    result = await db.execute(query)
    invoices = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=[_invoice_to_response(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db: AsyncSession = Depends(get_db)):
    """Get an invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _invoice_to_response(invoice)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an invoice."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    update_data = invoice_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status":
            value = DocumentStatus(value.value)
        setattr(invoice, key, value)

    await db.commit()
    await db.refresh(invoice)
    return _invoice_to_response(invoice)


@router.delete("/invoices/{invoice_id}", status_code=204)
async def delete_invoice(invoice_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    await db.delete(invoice)
    await db.commit()


# Delivery Note endpoints
@router.post("/delivery-notes", response_model=DeliveryNoteResponse, status_code=201)
async def create_delivery_note(
    dn_data: DeliveryNoteCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new delivery note."""
    existing = await db.execute(
        select(DeliveryNote).where(DeliveryNote.dn_number == dn_data.dn_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Delivery note number already exists")

    dn = DeliveryNote(
        dn_number=dn_data.dn_number,
        supplier_id=dn_data.supplier_id,
        supplier_name=dn_data.supplier_name,
        po_id=dn_data.po_id,
        delivery_date=dn_data.delivery_date,
        received_by=dn_data.received_by,
        total_amount=dn_data.total_amount,
        currency=dn_data.currency,
        notes=dn_data.notes,
        metadata_=dn_data.metadata_,
    )
    db.add(dn)
    await db.flush()

    for line_data in dn_data.lines:
        line = DeliveryNoteLine(
            delivery_note_id=dn.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_data.quantity * line_data.unit_price,
            uom=line_data.uom,
        )
        db.add(line)

    await db.commit()
    await db.refresh(dn)

    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn.id)
    )
    dn = result.scalar_one()

    return _delivery_note_to_response(dn)


@router.get("/delivery-notes", response_model=PaginatedResponse[DeliveryNoteResponse])
async def list_delivery_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    status: Optional[DocumentStatusEnum] = None,
    po_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all delivery notes with pagination."""
    query = select(DeliveryNote).options(selectinload(DeliveryNote.lines))
    count_query = select(func.count(DeliveryNote.id))

    if supplier_id:
        query = query.where(DeliveryNote.supplier_id == supplier_id)
        count_query = count_query.where(DeliveryNote.supplier_id == supplier_id)
    if status:
        query = query.where(DeliveryNote.status == DocumentStatus(status.value))
        count_query = count_query.where(DeliveryNote.status == DocumentStatus(status.value))
    if po_id:
        query = query.where(DeliveryNote.po_id == po_id)
        count_query = count_query.where(DeliveryNote.po_id == po_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(DeliveryNote.created_at.desc())
    result = await db.execute(query)
    dns = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=[_delivery_note_to_response(dn) for dn in dns],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/delivery-notes/{dn_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(dn_id: str, db: AsyncSession = Depends(get_db)):
    """Get a delivery note by ID."""
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn_id)
    )
    dn = result.scalar_one_or_none()
    if not dn:
        raise HTTPException(status_code=404, detail="Delivery note not found")
    return _delivery_note_to_response(dn)


@router.patch("/delivery-notes/{dn_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(
    dn_id: str,
    dn_data: DeliveryNoteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a delivery note."""
    result = await db.execute(
        select(DeliveryNote)
        .options(selectinload(DeliveryNote.lines))
        .where(DeliveryNote.id == dn_id)
    )
    dn = result.scalar_one_or_none()
    if not dn:
        raise HTTPException(status_code=404, detail="Delivery note not found")

    update_data = dn_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status":
            value = DocumentStatus(value.value)
        setattr(dn, key, value)

    await db.commit()
    await db.refresh(dn)
    return _delivery_note_to_response(dn)


@router.delete("/delivery-notes/{dn_id}", status_code=204)
async def delete_delivery_note(dn_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a delivery note."""
    result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == dn_id))
    dn = result.scalar_one_or_none()
    if not dn:
        raise HTTPException(status_code=404, detail="Delivery note not found")

    await db.delete(dn)
    await db.commit()


# Helper functions
def _po_to_response(po: PurchaseOrder) -> PurchaseOrderResponse:
    """Convert PO model to response schema."""
    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier_name,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        total_amount=po.total_amount,
        currency=po.currency,
        status=DocumentStatusEnum(po.status.value),
        notes=po.notes,
        metadata_=po.metadata_,
        lines=[_po_line_to_response(line) for line in po.lines],
        created_at=po.created_at,
        updated_at=po.updated_at,
    )


def _po_line_to_response(line: POLine) -> dict:
    """Convert PO Line model to response schema."""
    return {
        "id": line.id,
        "po_id": line.po_id,
        "line_number": line.line_number,
        "product_code": line.product_code,
        "description": line.description,
        "quantity": line.quantity,
        "unit_price": line.unit_price,
        "line_total": line.line_total,
        "uom": line.uom,
        "created_at": line.created_at,
        "updated_at": line.updated_at,
    }


def _invoice_to_response(invoice: Invoice) -> InvoiceResponse:
    """Convert Invoice model to response schema."""
    return InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        supplier_id=invoice.supplier_id,
        supplier_name=invoice.supplier_name,
        po_id=invoice.po_id,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        total_amount=invoice.total_amount,
        tax_amount=invoice.tax_amount,
        currency=invoice.currency,
        status=DocumentStatusEnum(invoice.status.value),
        notes=invoice.notes,
        metadata_=invoice.metadata_,
        lines=[_invoice_line_to_response(line) for line in invoice.lines],
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


def _invoice_line_to_response(line: InvoiceLine) -> dict:
    """Convert Invoice Line model to response schema."""
    return {
        "id": line.id,
        "invoice_id": line.invoice_id,
        "line_number": line.line_number,
        "product_code": line.product_code,
        "description": line.description,
        "quantity": line.quantity,
        "unit_price": line.unit_price,
        "line_total": line.line_total,
        "uom": line.uom,
        "created_at": line.created_at,
        "updated_at": line.updated_at,
    }


def _delivery_note_to_response(dn: DeliveryNote) -> DeliveryNoteResponse:
    """Convert Delivery Note model to response schema."""
    return DeliveryNoteResponse(
        id=dn.id,
        dn_number=dn.dn_number,
        supplier_id=dn.supplier_id,
        supplier_name=dn.supplier_name,
        po_id=dn.po_id,
        delivery_date=dn.delivery_date,
        received_by=dn.received_by,
        total_amount=dn.total_amount,
        currency=dn.currency,
        status=DocumentStatusEnum(dn.status.value),
        notes=dn.notes,
        metadata_=dn.metadata_,
        lines=[_dn_line_to_response(line) for line in dn.lines],
        created_at=dn.created_at,
        updated_at=dn.updated_at,
    )


def _dn_line_to_response(line: DeliveryNoteLine) -> dict:
    """Convert Delivery Note Line model to response schema."""
    return {
        "id": line.id,
        "delivery_note_id": line.delivery_note_id,
        "line_number": line.line_number,
        "product_code": line.product_code,
        "description": line.description,
        "quantity": line.quantity,
        "unit_price": line.unit_price,
        "line_total": line.line_total,
        "uom": line.uom,
        "created_at": line.created_at,
        "updated_at": line.updated_at,
    }
