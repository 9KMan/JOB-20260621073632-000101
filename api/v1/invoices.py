"""Invoice ingestion and CRUD endpoints."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import InvoiceIn, InvoiceListResponse, InvoiceOut
from core.database import get_session
from models.enums import DocumentStatus
from models.invoice import Invoice

router = APIRouter()


@router.post(
    "",
    response_model=InvoiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new invoice",
)
async def create_invoice(
    payload: InvoiceIn,
    session: AsyncSession = Depends(get_session),
) -> InvoiceOut:
    invoice = Invoice(
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        vendor_name=payload.vendor_name,
        currency=payload.currency.upper(),
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        source=payload.source,
        is_ocr=payload.is_ocr,
        notes=payload.notes,
        status=DocumentStatus.INGESTED,
    )
    for line in payload.lines:
        invoice.lines.append(_line_from_payload(line))  # type: ignore[arg-type]
    session.add(invoice)
    await session.flush()
    await session.refresh(invoice, attribute_names=["lines"])
    return InvoiceOut.model_validate(invoice)


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List invoices",
)
async def list_invoices(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[DocumentStatus] = Query(default=None, alias="status"),
    vendor_id: Optional[uuid.UUID] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> InvoiceListResponse:
    stmt = select(Invoice).order_by(Invoice.created_at.desc())
    count_stmt = select(func.count()).select_from(Invoice)
    if status_filter is not None:
        stmt = stmt.where(Invoice.status == status_filter)
        count_stmt = count_stmt.where(Invoice.status == status_filter)
    if vendor_id is not None:
        stmt = stmt.where(Invoice.vendor_id == vendor_id)
        count_stmt = count_stmt.where(Invoice.vendor_id == vendor_id)

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    items = [InvoiceOut.model_validate(row) for row in result.scalars().all()]
    return InvoiceListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
    summary="Get invoice by id",
)
async def get_invoice(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> InvoiceOut:
    invoice = await session.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return InvoiceOut.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an invoice",
)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    invoice = await session.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    invoice.status = DocumentStatus.CANCELLED
    await session.flush()


def _line_from_payload(line):  # type: ignore[no-untyped-def]
    from models.invoice import InvoiceLine

    return InvoiceLine(
        line_number=line.line_number,
        sku=line.sku,
        description=line.description,
        quantity=line.quantity,
        unit_price=line.unit_price,
        line_total=line.line_total,
        uom=line.uom,
        tax_amount=line.tax_amount,
    )
