# api/v1/matching.py
"""Matching engine endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.config import get_settings
from models import Invoice
from services.anchoring import AnchoringService
from services.cascade import CascadeService
from services.scoring import ScoringService
from api.schemas import (
    BaseResponse,
    MatchTriggerRequest,
    MatchResult,
    MatchDecisionRequest,
)

router = APIRouter()


@router.post(
    "/trigger",
    response_model=BaseResponse[MatchResult],
    summary="Trigger matching for an invoice",
    description="Run the matching engine on an invoice to find PO and DN matches.",
)
async def trigger_matching(
    request: MatchTriggerRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[MatchResult]:
    """Trigger the matching engine for an invoice."""
    settings = get_settings()
    
    # Get invoice
    result = await db.execute(
        select(Invoice).where(Invoice.id == request.invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {request.invoice_id} not found",
        )
    
    # Run matching pipeline
    try:
        # Layer 1: PO Anchoring
        anchoring_service = AnchoringService(db)
        anchoring_result = await anchoring_service.anchor_invoice_to_po(
            invoice, 
            match_all_lines=request.match_all_lines
        )
        
        if not anchoring_result.po_found:
            # No PO match possible
            return BaseResponse(
                success=True,
                data=MatchResult(
                    invoice_id=invoice.id,
                    invoice_number=invoice.invoice_number,
                    match_status="exception",
                    decision="no_match",
                    overall_score=0,
                    lines=[],
                    exception_reason="No matching purchase order found",
                ),
                message="No matching PO found",
            )
        
        # Layer 2: Line Matching Cascade
        cascade_service = CascadeService(db)
        cascade_result = await cascade_service.match_lines(
            invoice,
            anchoring_result.matched_po,
            anchoring_result.matched_lines,
        )
        
        # Layer 3: Scoring
        scoring_service = ScoringService(db, settings)
        score_result = await scoring_service.calculate_match_score(
            invoice,
            cascade_result,
        )
        
        # Determine decision based on score
        decision = scoring_service.determine_decision(score_result.overall_score)
        
        # Update invoice with match results
        invoice.match_score = score_result.overall_score
        invoice.match_decision = decision.value
        invoice.status = "matched" if decision.value == "auto_approved" else "exception"
        
        if decision.value == "exception":
            invoice.exception_reason = score_result.exception_reasons[0] if score_result.exception_reasons else None
        
        await db.commit()
        
        return BaseResponse(
            success=True,
            data=MatchResult(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                match_status="matched",
                decision=decision.value,
                overall_score=score_result.overall_score,
                lines=score_result.line_scores,
                exception_reason=invoice.exception_reason,
            ),
            message=f"Matching complete. Decision: {decision.value}",
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {str(e)}",
        )


@router.post(
    "/decision",
    response_model=BaseResponse[dict],
    summary="Submit match decision",
    description="Approve or reject a match decision for an invoice.",
)
async def submit_decision(
    request: MatchDecisionRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[dict]:
    """Submit a match decision for an invoice."""
    # Get invoice
    result = await db.execute(
        select(Invoice).where(Invoice.id == request.invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {request.invoice_id} not found",
        )
    
    # Update invoice with decision
    if request.decision == "approve":
        invoice.status = "approved"
        invoice.match_decision = "manual_approved"
    elif request.decision == "reject":
        invoice.status = "rejected"
        invoice.match_decision = "manual_rejected"
    elif request.decision == "exception":
        invoice.status = "exception"
        invoice.match_decision = "exception"
        invoice.exception_reason = request.reason
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision: {request.decision}",
        )
    
    await db.commit()
    
    return BaseResponse(
        success=True,
        data={
            "invoice_id": str(invoice.id),
            "status": invoice.status,
            "decision": invoice.match_decision,
        },
        message=f"Invoice {request.decision}d successfully",
    )


@router.get(
    "/result/{invoice_id}",
    response_model=BaseResponse[MatchResult],
    summary="Get match result for an invoice",
)
async def get_match_result(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BaseResponse[MatchResult]:
    """Get the matching result for an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )
    
    if not invoice.match_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No match result found for invoice {invoice_id}",
        )
    
    return BaseResponse(
        success=True,
        data=MatchResult(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            match_status=invoice.status,
            decision=invoice.match_decision or "pending",
            overall_score=invoice.match_score,
            lines=[],  # Would need to reconstruct from line scores
            exception_reason=invoice.exception_reason,
        ),
    )
