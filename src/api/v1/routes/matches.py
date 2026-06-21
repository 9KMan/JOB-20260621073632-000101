# src/api/v1/routes/matches.py
"""Matching Engine routes."""

from typing import Annotated
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_active_user
from src.models.user import User
from src.models.match import Match, MatchStatus, MatchDecision
from src.models.invoice import Invoice, InvoiceStatus
from src.api.v1.schemas.matches import (
    MatchResponse,
    MatchReview,
    MatchDecisionResponse,
    MatchStatistics,
)
from src.services.matching_service import MatchingService

router = APIRouter()


@router.post("/run", response_model=list[MatchResponse], status_code=status.HTTP_201_CREATED)
async def run_matching_engine(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[Match]:
    """Run the matching engine for an invoice."""
    matching_service = MatchingService(db)
    matches = await matching_service.run_matching(invoice_id)
    return matches


@router.get("/", response_model=list[MatchResponse])
async def list_matches(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    status: str | None = None,
    decision: str | None = None,
) -> list[Match]:
    """List all matches with pagination."""
    query = select(Match)

    if status:
        query = query.where(Match.status == status)
    if decision:
        query = query.where(Match.decision == decision)

    query = query.offset(skip).limit(limit).order_by(Match.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Match:
    """Get a match by ID."""
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    return match


@router.post("/{match_id}/review", response_model=MatchDecisionResponse)
async def review_match(
    match_id: UUID,
    review: MatchReview,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Review and update a match decision."""
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Update match with review decision
    match.status = MatchStatus.CONFIRMED.value if review.decision == "confirmed" else MatchStatus.REJECTED.value
    match.decision = review.decision
    match.reviewed_by = current_user.id
    match.reviewed_at = datetime.now(timezone.utc)
    match.review_notes = review.notes

    # Update invoice status
    invoice_result = await db.execute(select(Invoice).where(Invoice.id == match.invoice_id))
    invoice = invoice_result.scalar_one_or_none()
    if invoice:
        if review.decision == "confirmed":
            invoice.status = InvoiceStatus.APPROVED.value
        else:
            invoice.status = InvoiceStatus.REJECTED.value

    await db.commit()

    message = f"Match {review.decision} successfully"
    if review.decision == "confirmed":
        message += ". Invoice approved for payment."
    else:
        message += ". Invoice sent to dispute queue."

    return {
        "match_id": match_id,
        "decision": review.decision,
        "status": match.status,
        "message": message,
    }


@router.get("/statistics/summary", response_model=MatchStatistics)
async def get_match_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Get match statistics."""
    # Total matches
    total_result = await db.execute(select(func.count(Match.id)))
    total_matches = total_result.scalar() or 0

    # Status counts
    pending_result = await db.execute(
        select(func.count(Match.id)).where(Match.status == MatchStatus.PENDING.value)
    )
    pending = pending_result.scalar() or 0

    confirmed_result = await db.execute(
        select(func.count(Match.id)).where(Match.status == MatchStatus.CONFIRMED.value)
    )
    confirmed = confirmed_result.scalar() or 0

    rejected_result = await db.execute(
        select(func.count(Match.id)).where(Match.status == MatchStatus.REJECTED.value)
    )
    rejected = rejected_result.scalar() or 0

    # Decision counts
    auto_approved_result = await db.execute(
        select(func.count(Match.id)).where(Match.decision == MatchDecision.AUTO_APPROVED.value)
    )
    auto_approved = auto_approved_result.scalar() or 0

    human_review_result = await db.execute(
        select(func.count(Match.id)).where(Match.decision == MatchDecision.HUMAN_REVIEW.value)
    )
    human_review = human_review_result.scalar() or 0

    disputed_result = await db.execute(
        select(func.count(Match.id)).where(Match.decision == MatchDecision.DISPUTED.value)
    )
    disputed = disputed_result.scalar() or 0

    # Average score
    avg_result = await db.execute(select(func.avg(Match.total_score)))
    average_score = avg_result.scalar() or 0

    return {
        "total_matches": total_matches,
        "pending": pending,
        "confirmed": confirmed,
        "rejected": rejected,
        "auto_approved": auto_approved,
        "human_review": human_review,
        "disputed": disputed,
        "average_score": average_score,
    }


@router.get("/invoice/{invoice_id}/matches", response_model=list[MatchResponse])
async def get_invoice_matches(
    invoice_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[Match]:
    """Get all matches for an invoice."""
    result = await db.execute(
        select(Match)
        .where(Match.invoice_id == invoice_id)
        .order_by(Match.total_score.desc())
    )
    return result.scalars().all()
