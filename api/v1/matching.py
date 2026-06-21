# api/v1/matching.py
"""Matching engine trigger and decision endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    MatchResultResponse,
    MatchTriggerRequest,
    SuccessResponse,
)
from core.database import get_db
from models import Invoice, InvoiceLine
from services.anchoring import AnchoringService
from services.cascade import CascadeService

router = APIRouter()


@router.post(
    "/trigger",
    response_model=MatchResultResponse,
    summary="Trigger matching for an invoice",
)
async def trigger_matching(
    payload: MatchTriggerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchResultResponse:
    """Trigger the full matching engine for an invoice.

    The matching process consists of two layers:
    1. Anchoring — find candidate POs for the invoice header
    2. Cascade — match invoice lines to PO lines within the anchored PO

    Returns a decision per line and an overall score + decision.
    """
    # Load invoice with lines
    result = await db.execute(
        select(Invoice).where(Invoice.id == payload.invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {payload.invoice_id} not found",
        )

    # Refresh lines
    await db.refresh(invoice, attribute_names=["lines"])

    if not invoice.lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice has no line items to match",
        )

    # Layer 1: Anchoring — find best PO candidate(s)
    anchor_service = AnchoringService(db)
    anchored_po = await anchor_service.find_anchor_po(invoice)

    if anchored_po is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No matching PO found for this invoice",
        )

    # Layer 2: Cascade — match lines
    cascade_service = CascadeService(db)
    match_result = await cascade_service.match_invoice_to_po(
        invoice=invoice,
        po=anchored_po,
        force_rematch=payload.force_rematch,
    )

    return match_result


@router.post(
    "/trigger-all",
    response_model=SuccessResponse,
    summary="Trigger matching for all unmatched invoices",
)
async def trigger_all_matching(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse:
    """Trigger matching for all invoices in RECEIVED status."""
    from models.enums import InvoiceStatus

    result = await db.execute(
        select(Invoice).where(
            Invoice.status == InvoiceStatus.RECEIVED.value,
            Invoice.is_active == True,  # noqa: E712
        )
    )
    invoices = result.scalars().all()

    processed = 0
    for invoice in invoices:
        # Update status to matching
        invoice.status = InvoiceStatus.MATCHING.value

        # Refresh lines
        await db.refresh(invoice, attribute_names=["lines"])

        anchor_service = AnchoringService(db)
        anchored_po = await anchor_service.find_anchor_po(invoice)

        if anchored_po:
            cascade_service = CascadeService(db)
            await cascade_service.match_invoice_to_po(invoice, anchored_po)
            processed += 1

    await db.flush()
    return SuccessResponse(
        message=f"Matching triggered for {processed} invoices",
        detail={"total_unmatched": len(invoices), "processed": processed},
    )
