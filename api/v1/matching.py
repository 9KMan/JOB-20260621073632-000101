// api/v1/matching.py
"""Matching engine trigger and decision endpoints."""
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    MatchTriggerRequest,
    MatchResultResponse,
    ErrorResponse,
)
from core.config import settings
from core.database import get_db_session
from models import (
    Invoice,
    InvoiceStatus,
    MatchDecision,
    MatchStatus,
)
from services.anchoring import AnchoringService
from services.cascade import CascadeService
from services.scoring import ScoringService
from services.balances import BalanceService

router = APIRouter()


@router.post(
    "/trigger",
    response_model=MatchResultResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def trigger_matching(
    request: MatchTriggerRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MatchResultResponse:
    """
    Trigger the matching engine for an invoice.

    Executes the 3-layer matching process:
    1. Anchoring - Find matching PO
    2. Cascade - Match invoice lines to PO lines
    3. Scoring - Calculate match score and determine decision
    """
    # Get invoice
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(request.invoice_id),
            Invoice.is_deleted == False,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {request.invoice_id} not found",
        )

    # Update status to matching
    invoice.status = InvoiceStatus.MATCHING
    await db.flush()

    try:
        # Layer 1: Anchoring - Find matching PO
        anchoring_service = AnchoringService(db)
        anchor_result = await anchoring_service.find_anchor(invoice)

        if not anchor_result["po"]:
            # No matching PO found
            invoice.status = InvoiceStatus.EXCEPTION
            invoice.match_decision = MatchDecision.NO_MATCH.value
            await db.commit()

            return MatchResultResponse(
                invoice_id=str(invoice.id),
                match_decision=MatchDecision.NO_MATCH.value,
                match_score=None,
                match_confidence=None,
                po_id=None,
                dn_id=None,
                matched_lines=[],
                threshold_applied="none",
                exceptions=[{
                    "type": "missing_po",
                    "description": "No matching purchase order found",
                }],
            )

        # Layer 2: Cascade - Match lines
        cascade_service = CascadeService(db)
        cascade_result = await cascade_service.match_lines(
            invoice=invoice,
            po=anchor_result["po"],
            dn=anchor_result.get("dn"),
        )

        # Layer 3: Scoring - Calculate score and decision
        scoring_service = ScoringService(db)
        score_result = await scoring_service.calculate_match_score(
            invoice=invoice,
            po=anchor_result["po"],
            matched_lines=cascade_result["matched_lines"],
        )

        # Update invoice with matching results
        invoice.po_id = anchor_result["po"].id
        invoice.dn_id = anchor_result.get("dn", None)
        invoice.match_decision = score_result["decision"]
        invoice.match_score = Decimal(str(score_result["total_score"]))
        invoice.match_confidence = score_result["confidence"]

        # Update invoice status based on decision
        if score_result["decision"] == MatchDecision.AUTO_APPROVE.value:
            invoice.status = InvoiceStatus.AUTO_APPROVED
        elif score_result["decision"] == MatchDecision.MANUAL_REVIEW.value:
            invoice.status = InvoiceStatus.PENDING_REVIEW
        else:
            invoice.status = InvoiceStatus.EXCEPTION

        await db.commit()

        return MatchResultResponse(
            invoice_id=str(invoice.id),
            match_decision=score_result["decision"],
            match_score=Decimal(str(score_result["total_score"])),
            match_confidence=score_result["confidence"],
            po_id=str(invoice.po_id),
            dn_id=str(invoice.dn_id) if invoice.dn_id else None,
            matched_lines=cascade_result["matched_lines"],
            threshold_applied=score_result["threshold_used"],
            exceptions=score_result.get("exceptions", []),
        )

    except Exception as e:
        invoice.status = InvoiceStatus.EXCEPTION
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matching failed: {str(e)}",
        )


@router.get(
    "/decision/{invoice_id}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_match_decision(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """
    Get the current matching decision for an invoice.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(invoice_id),
            Invoice.is_deleted == False,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return {
        "invoice_id": str(invoice.id),
        "status": invoice.status.value,
        "decision": invoice.match_decision,
        "score": float(invoice.match_score) if invoice.match_score else None,
        "confidence": invoice.match_confidence,
        "po_id": str(invoice.po_id) if invoice.po_id else None,
        "dn_id": str(invoice.dn_id) if invoice.dn_id else None,
    }


@router.post(
    "/approve/{invoice_id}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def approve_invoice(
    invoice_id: str,
    approved_by: str = Query(..., description="User approving the invoice"),
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """
    Manually approve an invoice after review.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(invoice_id),
            Invoice.is_deleted == False,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    if invoice.status not in [
        InvoiceStatus.PENDING_REVIEW,
        InvoiceStatus.EXCEPTION,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice status {invoice.status} does not allow approval",
        )

    from datetime import datetime, timezone

    invoice.status = InvoiceStatus.APPROVED
    invoice.approved_by = approved_by
    invoice.approved_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "invoice_id": str(invoice.id),
        "status": invoice.status.value,
        "approved_by": approved_by,
        "approved_at": invoice.approved_at.isoformat(),
    }


@router.post(
    "/reject/{invoice_id}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def reject_invoice(
    invoice_id: str,
    rejected_by: str = Query(..., description="User rejecting the invoice"),
    reason: str = Query(..., description="Rejection reason"),
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """
    Manually reject an invoice.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == uuid.UUID(invoice_id),
            Invoice.is_deleted == False,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    invoice.status = InvoiceStatus.REJECTED
    await db.commit()

    return {
        "invoice_id": str(invoice.id),
        "status": invoice.status.value,
        "rejected_by": rejected_by,
        "reason": reason,
    }
