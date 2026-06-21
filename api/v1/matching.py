"""Matching engine trigger and decision retrieval."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import LineDecisionOut, MatchRequest, MatchResultOut
from core.database import get_session
from models.enums import DecisionType, DocumentStatus
from models.invoice import Invoice
from services.anchoring import anchor_invoice
from services.cascade import cascade_match
from services.scoring import aggregate_overall_score, route_decision

router = APIRouter()


@router.post(
    "/run",
    response_model=MatchResultOut,
    summary="Run the matching cascade for an invoice",
)
async def run_matching(
    payload: MatchRequest,
    session: AsyncSession = Depends(get_session),
) -> MatchResultOut:
    invoice = await session.get(Invoice, payload.invoice_id, options=[])
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    if not payload.force and invoice.status not in {
        DocumentStatus.INGESTED,
        DocumentStatus.PROCESSING,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice in status {invoice.status.value} is not eligible for matching",
        )

    # Eager-load lines so cascade_match can iterate without lazy IO.
    line_rows = (
        await session.execute(select(Invoice).where(Invoice.id == invoice.id))
    ).scalar_one()

    anchor_result = await anchor_invoice(session, line_rows)
    cascade_result = await cascade_match(session, line_rows, anchor_result)
    line_decisions = [
        LineDecisionOut(
            invoice_line_id=line.invoice_line_id,
            purchase_order_line_id=line.purchase_order_line_id,
            score=line.score,
            decision=line.decision,
            layer=line.layer,
            reasons=line.reasons,
        )
        for line in cascade_result.line_decisions
    ]
    overall_score = aggregate_overall_score(line_decisions)
    overall_decision = route_decision(overall_score, line_decisions)

    invoice.status = DocumentStatus.PROCESSING
    await session.flush()

    return MatchResultOut(
        invoice_id=invoice.id,
        overall_score=overall_score,
        overall_decision=overall_decision,
        decided_at=datetime.now(timezone.utc),
        line_decisions=line_decisions,
    )


@router.get(
    "/decisions/{invoice_id}",
    response_model=MatchResultOut,
    summary="Retrieve the most recent matching decision for an invoice",
)
async def get_decision(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> MatchResultOut:
    """Decisions are derived (no separate table in this phase); rerun on demand.

    Real systems persist a decision table; here we return a deterministic
    placeholder so the endpoint contract is stable.
    """
    invoice = await session.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return MatchResultOut(
        invoice_id=invoice.id,
        overall_score=0.0,
        overall_decision=DecisionType.NEEDS_REVIEW,
        decided_at=datetime.now(timezone.utc),
        line_decisions=[],
    )
