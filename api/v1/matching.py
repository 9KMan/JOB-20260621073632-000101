// api/v1/matching.py
"""Matching engine trigger and decision endpoints."""

import logging
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    APIErrorResponse,
    MatchDecisionUpdate,
    MatchResult,
    MatchTriggerRequest,
    MatchLineResult,
)
from core.database import get_db_session
from models import Invoice, InvoiceStatus, MatchDecision
from services.anchoring import AnchoringService
from services.cascade import CascadeService
from services.scoring import ScoringService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/trigger",
    response_model=MatchResult,
    responses={
        404: {"model": APIErrorResponse},
        409: {"model": APIErrorResponse},
    },
)
async def trigger_matching(
    payload: MatchTriggerRequest,
    session: AsyncSession = Depends(get_db_session),
) -> MatchResult:
    """
    Trigger the matching engine for a single invoice.

    The engine runs in two layers:
      1. Anchoring — find/confirm the PO reference
      2. Cascade  — match invoice lines to PO lines and DN lines

    Then the scoring service computes the overall match confidence
    and routes the invoice to the appropriate decision bucket.
    """
    result = await session.execute(select(Invoice).where(Invoice.id == payload.invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == InvoiceStatus.MATCHING_IN_PROGRESS and not payload.force_rerun:
        raise HTTPException(
            status_code=409,
            detail="Matching is already in progress. Set force_rerun=true to override.",
        )

    # Mark as in-progress
    invoice.status = InvoiceStatus.MATCHING_IN_PROGRESS
    await session.commit()

    try:
        # ── Layer 1: Anchoring ────────────────────────────────────────────────
        anchor_svc = AnchoringService(session)
        anchor_result = await anchor_svc.run(invoice)

        # ── Layer 2: Cascade ──────────────────────────────────────────────────
        cascade_svc = CascadeService(session)
        cascade_result = await cascade_svc.run(invoice)

        # ── Scoring ───────────────────────────────────────────────────────────
        scoring_svc = ScoringService(session)
        score_result = await scoring_svc.run(invoice, anchor_result, cascade_result)

        # ── Commit decision ───────────────────────────────────────────────────
        invoice.match_score = score_result.overall_score
        invoice.match_decision = score_result.decision.value
        invoice.match_decision_at = datetime.now(timezone.utc)
        invoice.match_decision_by = "matching_engine"
        invoice.status = InvoiceStatus.MATCHED if score_result.decision != MatchDecision.EXCEPTION else InvoiceStatus.EXCEPTION

        await session.commit()

        logger.info(
            "Matching complete for invoice %s: score=%.2f decision=%s",
            invoice.id,
            score_result.overall_score,
            score_result.decision.value,
        )

        return MatchResult(
            invoice_id=invoice.id,
            decision=score_result.decision.value,
            overall_score=score_result.overall_score,
            score_band=score_result.score_band.value,
            line_results=[
                MatchLineResult(
                    invoice_line_id=lr.invoice_line_id,
                    po_line_id=lr.po_line_id,
                    delivery_note_line_id=lr.delivery_note_line_id,
                    match_score=lr.match_score,
                    match_band=lr.match_band,
                    price_match=lr.price_match,
                    qty_match=lr.qty_match,
                    matched_qty=lr.matched_qty,
                    cross_ref_id=lr.cross_ref_id,
                )
                for lr in score_result.line_results
            ],
            run_at=datetime.now(timezone.utc),
        )

    except Exception as exc:
        await session.rollback()
        logger.exception("Matching failed for invoice %s: %s", payload.invoice_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Matching engine failed: {exc}",
        )


@router.patch("/decision")
async def update_matching_decision(
    payload: MatchDecisionUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Allow an operator to override a matching decision (approve / reject)
    after manual review.
    """
    result = await session.execute(select(Invoice).where(Invoice.id == payload.invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if payload.decision == "approved":
        invoice.status = InvoiceStatus.APPROVED
    elif payload.decision == "rejected":
        invoice.status = InvoiceStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'rejected'")

    if payload.override_score is not None:
        invoice.match_score = payload.override_score
    invoice.match_decision_by = "manual_override"
    invoice.match_decision_at = datetime.now(timezone.utc)

    await session.commit()
    logger.info("Decision override for invoice %s: %s by %s",
                invoice.id, payload.decision, invoice.match_decision_by)
    return {"message": "Decision updated", "invoice_id": str(invoice.id)}


@router.get("/result/{invoice_id}", response_model=MatchResult)
async def get_matching_result(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MatchResult:
    """Return the cached matching result for an invoice."""
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.match_decision is None:
        raise HTTPException(
            status_code=404,
            detail="No matching result found for this invoice. Trigger matching first.",
        )

    return MatchResult(
        invoice_id=invoice.id,
        decision=invoice.match_decision,
        overall_score=invoice.match_score or 0.0,
        score_band="unknown",
        line_results=[],
        run_at=invoice.match_decision_at or datetime.now(timezone.utc),
    )
