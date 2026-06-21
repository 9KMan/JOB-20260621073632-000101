// src/api/routes/matching.py
"""Matching engine routes."""
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db
from app.api.schemas.matching import (
    MatchRequest,
    MatchResultResponse,
    MatchResultDetailResponse,
    MatchScoreResponse,
    MatchingSummaryResponse,
    ManualReviewRequest,
    BalanceLedgerResponse,
    MatchStatusEnum,
)
from app.models.matching import MatchResult, MatchScore, MatchStatus, MatchType
from app.models.balance import BalanceLedger, BalanceType
from app.services.matching.anchor_service import AnchorService
from app.services.matching.cascade_service import CascadeService
from app.services.matching.balance_service import BalanceService
from app.services.matching.decision_engine import DecisionEngine

router = APIRouter()


@router.post("/match", response_model=MatchResultDetailResponse)
async def initiate_matching(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Initiate matching for provided documents."""
    # Validate at least one document is provided
    if not any([request.invoice_id, request.delivery_note_id, request.po_id]):
        raise HTTPException(
            status_code=400,
            detail="At least one document ID (invoice_id, delivery_note_id, or po_id) is required",
        )

    # Perform matching
    anchor_service = AnchorService(db)
    cascade_service = CascadeService(db)
    decision_engine = DecisionEngine(db)
    balance_service = BalanceService(db)

    # Step 1: Anchor the PO if available
    po = None
    if request.po_id:
        result = await db.execute(
            select(MatchResult).options(selectinload(MatchResult.scores)).where(MatchResult.id == request.po_id)
        )
        # If po_id provided, get the PO
        from app.models.document import PurchaseOrder
        result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == request.po_id))
        po = result.scalar_one_or_none()
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

    # Step 2: Cascade matching
    match_result = await cascade_service.match_documents(
        invoice_id=request.invoice_id,
        delivery_note_id=request.delivery_note_id,
        po_id=request.po_id,
        match_type=request.match_type.value if request.match_type else None,
    )

    # Step 3: Make decision
    decision = await decision_engine.make_decision(match_result)

    # Update match result with decision
    match_result.decision = decision.decision
    match_result.decision_reason = decision.reason
    if decision.auto_approve:
        match_result.status = MatchStatus.AUTO_APPROVED

    # Step 4: Update balance ledger if matched
    if decision.decision == "CONFIRMED":
        await balance_service.update_balances(match_result)

    await db.commit()

    # Reload with scores
    result = await db.execute(
        select(MatchResult)
        .options(selectinload(MatchResult.scores))
        .where(MatchResult.id == match_result.id)
    )
    match_result = result.scalar_one()

    return _match_result_to_detail_response(match_result)


@router.get("/match-results", response_model=MatchingSummaryResponse)
async def list_match_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    invoice_id: Optional[str] = None,
    delivery_note_id: Optional[str] = None,
    po_id: Optional[str] = None,
    status: Optional[MatchStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all match results with filtering and pagination."""
    query = select(MatchResult)
    count_query = select(func.count(MatchResult.id))

    if invoice_id:
        query = query.where(MatchResult.invoice_id == invoice_id)
        count_query = count_query.where(MatchResult.invoice_id == invoice_id)
    if delivery_note_id:
        query = query.where(MatchResult.delivery_note_id == delivery_note_id)
        count_query = count_query.where(MatchResult.delivery_note_id == delivery_note_id)
    if po_id:
        query = query.where(MatchResult.po_id == po_id)
        count_query = count_query.where(MatchResult.po_id == po_id)
    if status:
        query = query.where(MatchResult.status == MatchStatus(status.value))
        count_query = count_query.where(MatchResult.status == MatchStatus(status.value))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(MatchResult.created_at.desc())
    result = await db.execute(query)
    matches = result.scalars().all()

    # Calculate summary
    auto_approved = sum(1 for m in matches if m.status == MatchStatus.AUTO_APPROVED)
    pending_review = sum(1 for m in matches if m.status == MatchStatus.HUMAN_REVIEW)
    rejected = sum(1 for m in matches if m.status == MatchStatus.REJECTED)
    disputed = sum(1 for m in matches if m.status == MatchStatus.DISPUTED)
    avg_score = sum(m.total_score for m in matches) / len(matches) if matches else Decimal("0")
    total_amount = sum(
        m.invoice_amount or Decimal("0") for m in matches if m.invoice_amount
    )

    total_pages = (total + page_size - 1) // page_size

    return MatchingSummaryResponse(
        total_matches=total,
        auto_approved=auto_approved,
        pending_review=pending_review,
        rejected=rejected,
        disputed=disputed,
        average_score=avg_score,
        total_amount_involved=total_amount,
        results=[_match_result_to_response(m) for m in matches],
    )


@router.get("/match-results/{match_id}", response_model=MatchResultDetailResponse)
async def get_match_result(match_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific match result with detailed scores."""
    result = await db.execute(
        select(MatchResult)
        .options(selectinload(MatchResult.scores))
        .where(MatchResult.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match result not found")
    return _match_result_to_detail_response(match)


@router.post("/match-results/{match_id}/review", response_model=MatchResultResponse)
async def submit_manual_review(
    match_id: str,
    review: ManualReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit manual review decision for a match result."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(MatchResult).where(MatchResult.id == match_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match result not found")

    if match.status not in [MatchStatus.PENDING, MatchStatus.HUMAN_REVIEW]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot review match in status {match.status.value}",
        )

    # Update with review decision
    match.status = MatchStatus.CONFIRMED if review.decision == "CONFIRMED" else MatchStatus.REJECTED
    match.reviewed_by = review.reviewed_by
    match.reviewed_at = datetime.now(timezone.utc)
    match.review_notes = review.notes

    # Update document statuses
    if review.decision == "CONFIRMED":
        await _update_document_statuses_on_confirmation(db, match)

    await db.commit()
    await db.refresh(match)
    return _match_result_to_response(match)


@router.get("/balances", response_model=list[BalanceLedgerResponse])
async def list_balances(
    po_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    delivery_note_id: Optional[str] = None,
    is_settled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List balance ledger entries."""
    query = select(BalanceLedger)

    if po_id:
        query = query.where(BalanceLedger.po_id == po_id)
    if invoice_id:
        query = query.where(BalanceLedger.invoice_id == invoice_id)
    if delivery_note_id:
        query = query.where(BalanceLedger.delivery_note_id == delivery_note_id)
    if is_settled is not None:
        query = query.where(BalanceLedger.is_settled == is_settled)

    query = query.order_by(BalanceLedger.effective_date.desc())
    result = await db.execute(query)
    balances = result.scalars().all()

    return [_balance_to_response(b) for b in balances]


@router.get("/balances/{balance_id}", response_model=BalanceLedgerResponse)
async def get_balance(balance_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific balance ledger entry."""
    result = await db.execute(
        select(BalanceLedger).where(BalanceLedger.id == balance_id)
    )
    balance = result.scalar_one_or_none()
    if not balance:
        raise HTTPException(status_code=404, detail="Balance entry not found")
    return _balance_to_response(balance)


# Helper functions
def _match_result_to_response(match: MatchResult) -> MatchResultResponse:
    """Convert MatchResult model to response schema."""
    return MatchResultResponse(
        id=match.id,
        invoice_id=match.invoice_id,
        delivery_note_id=match.delivery_note_id,
        po_id=match.po_id,
        match_type=match.match_type,
        status=MatchStatusEnum(match.status.value),
        total_score=match.total_score,
        line_score=match.line_score,
        amount_score=match.amount_score,
        date_score=match.date_score,
        po_amount=match.po_amount,
        invoice_amount=match.invoice_amount,
        delivery_note_amount=match.delivery_note_amount,
        amount_variance=match.amount_variance,
        po_quantity=match.po_quantity,
        invoice_quantity=match.invoice_quantity,
        delivery_note_quantity=match.delivery_note_quantity,
        quantity_variance=match.quantity_variance,
        decision=match.decision,
        decision_reason=match.decision_reason,
        reviewed_by=match.reviewed_by,
        reviewed_at=match.reviewed_at,
        review_notes=match.review_notes,
        created_at=match.created_at,
        updated_at=match.updated_at,
    )


def _match_result_to_detail_response(match: MatchResult) -> MatchResultDetailResponse:
    """Convert MatchResult model to detailed response schema."""
    return MatchResultDetailResponse(
        **_match_result_to_response(match).model_dump(),
        scores=[_score_to_response(s) for s in match.scores],
    )


def _score_to_response(score: MatchScore) -> MatchScoreResponse:
    """Convert MatchScore model to response schema."""
    return MatchScoreResponse(
        id=score.id,
        po_line_id=score.po_line_id,
        invoice_line_id=score.invoice_line_id,
        delivery_note_line_id=score.delivery_note_line_id,
        product_code_match=score.product_code_match,
        po_quantity=score.po_quantity,
        matched_quantity=score.matched_quantity,
        quantity_match_score=score.quantity_match_score,
        po_amount=score.po_amount,
        matched_amount=score.matched_amount,
        amount_match_score=score.amount_match_score,
        line_score=score.line_score,
        is_matched=score.is_matched,
        variance_reason=score.variance_reason,
    )


def _balance_to_response(balance: BalanceLedger) -> BalanceLedgerResponse:
    """Convert BalanceLedger model to response schema."""
    return BalanceLedgerResponse(
        id=balance.id,
        po_id=balance.po_id,
        invoice_id=balance.invoice_id,
        delivery_note_id=balance.delivery_note_id,
        balance_type=balance.balance_type.value,
        original_amount=balance.original_amount,
        original_quantity=balance.original_quantity,
        remaining_amount=balance.remaining_amount,
        remaining_quantity=balance.remaining_quantity,
        billed_amount=balance.billed_amount,
        billed_quantity=balance.billed_quantity,
        is_settled=balance.is_settled,
        settlement_date=balance.settlement_date,
        effective_date=balance.effective_date,
    )


async def _update_document_statuses_on_confirmation(db: AsyncSession, match: MatchResult):
    """Update document statuses when a match is confirmed."""
    from app.models.document import DocumentStatus, Invoice, DeliveryNote, PurchaseOrder

    if match.invoice_id:
        result = await db.execute(select(Invoice).where(Invoice.id == match.invoice_id))
        invoice = result.scalar_one_or_none()
        if invoice:
            invoice.status = DocumentStatus.CONFIRMED

    if match.delivery_note_id:
        result = await db.execute(select(DeliveryNote).where(DeliveryNote.id == match.delivery_note_id))
        dn = result.scalar_one_or_none()
        if dn:
            dn.status = DocumentStatus.CONFIRMED

    if match.po_id:
        result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == match.po_id))
        po = result.scalar_one_or_none()
        if po:
            po.status = DocumentStatus.CONFIRMED
