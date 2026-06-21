# api/v1/matching.py
"""Matching engine trigger and decision endpoints."""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    MatchRequest,
    MatchResult,
    MatchResultLine,
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)
from core.database import get_db
from core.config import settings
from models import Invoice, InvoiceStatus, MatchDecision, MatchConfidence
from services.anchoring import AnchoringService
from services.cascade import CascadeService
from services.scoring import ScoringService
from services.balances import BalanceLedgerService

router = APIRouter()


@router.post(
    "/trigger",
    response_model=MatchResult,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def trigger_matching(
    request: MatchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchResult:
    """Trigger the matching engine for an invoice."""
    start_time = time.time()

    result = await db.execute(
        select(Invoice).where(Invoice.id == request.invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {request.invoice_id} not found",
        )

    if invoice.status == InvoiceStatus.MATCHED.value and not request.force_rematch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is already matched. Set force_rematch=true to rematch.",
        )

    invoice.status = InvoiceStatus.MATCHING.value
    await db.flush()

    try:
        anchoring_service = AnchoringService(db)
        cascade_service = CascadeService(db)
        scoring_service = ScoringService(db)

        anchored_lines = await anchoring_service.anchor_invoice_to_pos(invoice)

        matched_lines = await cascade_service.cascade_match(anchored_lines)

        scoring_service.update_invoice_lines(matched_lines)

        result_lines: list[MatchResultLine] = []
        exceptions: list[str] = []
        total_score = 0.0
        matched_count = 0

        for line in matched_lines:
            line_result = MatchResultLine(
                line_number=line.line_number,
                description=line.description,
                invoice_quantity=line.quantity,
                invoice_unit_price=line.unit_price,
                po_line_id=line.po_line_id,
                po_description=line.po_line.description if line.po_line else None,
                po_quantity=line.po_line.ordered_quantity if line.po_line else None,
                po_unit_price=line.po_line.unit_price if line.po_line else None,
                quantity_variance_pct=line.quantity_variance_pct,
                price_variance_pct=line.price_variance_pct,
                match_score=line.match_score or 0.0,
                match_confidence=line.match_confidence or MatchConfidence.NONE.value,
                match_reason=line.match_reason,
            )
            result_lines.append(line_result)

            if line.match_score and line.match_score > 0:
                total_score += line.match_score
                matched_count += 1

            if line.match_reason:
                exceptions.append(line.match_reason)

        if matched_count > 0:
            overall_score = total_score / matched_count
        else:
            overall_score = 0.0

        decision = scoring_service.determine_decision(overall_score)
        auto_approved = decision == MatchDecision.AUTO_APPROVED.value

        if auto_approved:
            invoice.status = InvoiceStatus.APPROVED.value
        elif overall_score >= settings.threshold.low:
            invoice.status = InvoiceStatus.EXCEPTION.value
        else:
            invoice.status = InvoiceStatus.REJECTED.value

        await db.flush()

        processing_time = int((time.time() - start_time) * 1000)

        return MatchResult(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            decision=decision,
            overall_score=round(overall_score, 2),
            auto_approved=auto_approved,
            lines=result_lines,
            exceptions=exceptions,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        invoice.status = InvoiceStatus.EXCEPTION.value
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {str(e)}",
        )


@router.get(
    "/decision/{invoice_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_match_decision(
    invoice_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get the matching decision for an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.is_deleted == False)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    lines_with_scores = [line for line in invoice.lines if line.match_score is not None]

    if lines_with_scores:
        avg_score = sum(line.match_score for line in lines_with_scores) / len(lines_with_scores)
    else:
        avg_score = 0.0

    scoring_service = ScoringService(db)
    decision = scoring_service.determine_decision(avg_score)

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "average_match_score": round(avg_score, 2),
        "decision": decision,
        "line_count": len(invoice.lines),
        "matched_line_count": sum(1 for line in lines_with_scores if line.is_matched),
    }
