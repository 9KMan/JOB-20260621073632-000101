# api/v1/matching.py
"""Matching engine trigger and decision endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    MatchTriggerRequest,
    MatchDecisionResponse,
    MatchScoreDetail,
    ErrorResponse,
)
from core.database import get_db
from core.config import get_settings
from models import Invoice, InvoiceStatus, MatchDecision
from services.anchoring import AnchoringService
from services.cascade import CascadeService
from services.scoring import ScoringService

router = APIRouter()


@router.post(
    "/trigger",
    response_model=MatchDecisionResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def trigger_matching(
    request: MatchTriggerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchDecisionResponse:
    """Trigger the matching engine for an invoice."""
    settings = get_settings()

    result = await db.execute(select(Invoice).where(Invoice.id == request.invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {request.invoice_id} not found",
        )

    if not request.force_rematch and invoice.status in [
        InvoiceStatus.MATCHED.value,
        InvoiceStatus.APPROVED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice is already in {invoice.status} status",
        )

    invoice.status = InvoiceStatus.MATCHING.value
    await db.flush()

    try:
        anchoring_service = AnchoringService(db)
        matched_po, anchor_score = await anchoring_service.anchor_invoice_to_po(invoice)

        if not matched_po:
            invoice.status = InvoiceStatus.EXCEPTION.value
            await db.flush()
            return MatchDecisionResponse(
                invoice_id=invoice.id,
                decision=MatchDecision.NO_MATCH.value,
                confidence_score=Decimal("0.0"),
                score_breakdown=[],
                matched_po_id=None,
                matched_po_number=None,
                matched_lines=[],
                exceptions=["No matching purchase order found"],
                match_timestamp=datetime.now(timezone.utc),
            )

        cascade_service = CascadeService(db)
        line_matches = await cascade_service.cascade_match_lines(invoice, matched_po)

        scoring_service = ScoringService(db)
        score_breakdown, total_score = await scoring_service.calculate_match_score(
            invoice, matched_po, line_matches, anchor_score
        )

        decision = scoring_service.determine_decision(
            total_score,
            settings.thresholds.threshold_high,
            settings.thresholds.threshold_mid,
            settings.thresholds.threshold_low,
        )

        if decision == MatchDecision.AUTO_APPROVED.value:
            invoice.status = InvoiceStatus.APPROVED.value
            invoice.approved_at = datetime.now(timezone.utc)
        elif decision == MatchDecision.ONE_CLICK_REVIEW.value:
            invoice.status = InvoiceStatus.PENDING.value
        else:
            invoice.status = InvoiceStatus.EXCEPTION.value

        await db.flush()

        return MatchDecisionResponse(
            invoice_id=invoice.id,
            decision=decision,
            confidence_score=total_score,
            score_breakdown=[
                MatchScoreDetail(
                    component=sd.component,
                    score=sd.score,
                    weight=sd.weight,
                    weighted_score=sd.weighted_score,
                )
                for sd in score_breakdown
            ],
            matched_po_id=matched_po.id,
            matched_po_number=matched_po.po_number,
            matched_lines=[
                {
                    "invoice_line_id": lm.invoice_line_id,
                    "po_line_id": lm.po_line_id,
                    "match_score": float(lm.match_score),
                }
                for lm in line_matches
            ],
            exceptions=[],
            match_timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        invoice.status = InvoiceStatus.EXCEPTION.value
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching engine error: {str(e)}",
        )


@router.get(
    "/decision/{invoice_id}",
    response_model=MatchDecisionResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_match_decision(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchDecisionResponse:
    """Get the current match decision for an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )

    return MatchDecisionResponse(
        invoice_id=invoice.id,
        decision=invoice.status,
        confidence_score=Decimal("0.0"),
        score_breakdown=[],
        matched_po_id=None,
        matched_po_number=invoice.po_reference,
        matched_lines=[],
        exceptions=[],
        match_timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/approve/{invoice_id}",
    response_model=MatchDecisionResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def approve_invoice(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchDecisionResponse:
    """Approve a matched invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )

    if invoice.status != InvoiceStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice is not in pending status (current: {invoice.status})",
        )

    invoice.status = InvoiceStatus.APPROVED.value
    invoice.approved_at = datetime.now(timezone.utc)
    await db.flush()

    return MatchDecisionResponse(
        invoice_id=invoice.id,
        decision=MatchDecision.AUTO_APPROVED.value,
        confidence_score=Decimal("0.0"),
        score_breakdown=[],
        matched_po_id=None,
        matched_po_number=invoice.po_reference,
        matched_lines=[],
        exceptions=[],
        match_timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/reject/{invoice_id}",
    response_model=MatchDecisionResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def reject_invoice(
    invoice_id: str,
    reason: str = Query(..., description="Rejection reason"),
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchDecisionResponse:
    """Reject a matched invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found",
        )

    invoice.status = InvoiceStatus.REJECTED.value
    invoice.rejected_at = datetime.now(timezone.utc)
    invoice.rejection_reason = reason
    await db.flush()

    return MatchDecisionResponse(
        invoice_id=invoice.id,
        decision=MatchDecision.REJECTED.value,
        confidence_score=Decimal("0.0"),
        score_breakdown=[],
        matched_po_id=None,
        matched_po_number=invoice.po_reference,
        matched_lines=[],
        exceptions=[reason],
        match_timestamp=datetime.now(timezone.utc),
    )
