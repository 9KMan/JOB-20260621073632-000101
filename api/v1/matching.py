# api/v1/matching.py
"""Matching engine endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from api.schemas import ErrorResponse, MatchingResponse, MatchingResult
from core.database import get_db
from core.config import settings
from models import DecisionType, Invoice, InvoiceStatus, MatchStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter()

MatchDB = Annotated[AsyncSession, get_db]


class TriggerMatchingRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: UUID
    force_rerun: bool = False


@router.post(
    "/trigger",
    response_model=MatchingResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def trigger_matching(
    request: TriggerMatchingRequest,
    db: MatchDB,
) -> MatchingResponse:
    """Trigger the matching engine for an invoice."""
    # Load invoice with lines
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(
            Invoice.id == request.invoice_id,
            Invoice.is_deleted == False,  # noqa: E712
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {request.invoice_id} not found",
        )

    if invoice.status == InvoiceStatus.MATCHING.value and not request.force_rerun:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Matching already in progress for this invoice",
        )

    # Import services lazily to avoid circular imports
    from services.anchoring import AnchoringService
    from services.cascade import CascadeService
    from services.scoring import ScoringService

    # Update status to matching
    invoice.status = InvoiceStatus.MATCHING.value
    await db.flush()

    # Layer 1: PO Anchoring
    anchoring_service = AnchoringService(db)
    anchor_results = await anchoring_service.anchor_invoice(invoice)

    # Layer 2: Cascade line matching
    cascade_service = CascadeService(db)
    cascade_results = await cascade_service.match_lines(invoice, anchor_results)

    # Layer 3: Scoring
    scoring_service = ScoringService(db)
    scored_results = await scoring_service.score_matches(cascade_results)

    # Calculate overall decision
    total_lines = len(invoice.lines)
    matched_lines = sum(1 for r in scored_results if r.po_line_id is not None)
    avg_score = (
        sum(r.match_score for r in scored_results) / total_lines
        if total_lines > 0
        else 0.0
    )

    # Determine decision based on thresholds
    if avg_score >= settings.threshold.threshold_high:
        decision = DecisionType.AUTO_APPROVE.value
        invoice.status = InvoiceStatus.APPROVED.value
        invoice.approved_at = datetime.now(timezone.utc)
    elif avg_score >= settings.threshold.threshold_mid:
        decision = DecisionType.MANUAL_REVIEW.value
        invoice.status = InvoiceStatus.MATCHED.value
    elif avg_score >= settings.threshold.threshold_low:
        decision = DecisionType.EXCEPTION.value
        invoice.status = InvoiceStatus.EXCEPTION.value
    else:
        decision = DecisionType.EXCEPTION.value
        invoice.status = InvoiceStatus.EXCEPTION.value

    invoice.matched_at = datetime.now(timezone.utc)

    # Build matching results
    matching_results = []
    for r in scored_results:
        match_type = None
        if r.po_line_id:
            if r.match_score >= settings.threshold.threshold_high:
                match_type = "direct"
            elif r.match_score >= settings.threshold.threshold_mid:
                match_type = "fuzzy"
            else:
                match_type = "partial"

        matching_results.append(
            MatchingResult(
                invoice_line_id=r.invoice_line_id,
                po_line_id=r.po_line_id,
                match_score=r.match_score,
                decision=r.decision,
                match_type=match_type,
            )
        )

    await db.commit()

    return MatchingResponse(
        invoice_id=invoice.id,
        status=invoice.status,
        total_lines=total_lines,
        matched_lines=matched_lines,
        match_score=avg_score,
        decision=decision,
        results=matching_results,
        processed_at=datetime.now(timezone.utc),
    )


@router.get(
    "/decision/{invoice_id}",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_matching_decision(
    invoice_id: UUID,
    db: MatchDB,
) -> dict:
    """Get the matching decision for an invoice."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.is_deleted == False,  # noqa: E712
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Calculate decision based on current status
    if invoice.status == InvoiceStatus.APPROVED.value:
        decision = DecisionType.AUTO_APPROVE.value
    elif invoice.status == InvoiceStatus.MATCHED.value:
        decision = DecisionType.MANUAL_REVIEW.value
    elif invoice.status == InvoiceStatus.EXCEPTION.value:
        decision = DecisionType.EXCEPTION.value
    else:
        decision = DecisionType.ANCHOR.value

    return {
        "invoice_id": str(invoice.id),
        "status": invoice.status,
        "decision": decision,
        "matched_at": invoice.matched_at.isoformat() if invoice.matched_at else None,
        "approved_at": invoice.approved_at.isoformat() if invoice.approved_at else None,
    }
