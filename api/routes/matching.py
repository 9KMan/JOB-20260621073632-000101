// api/routes/matching.py
"""Matching routes for 3-way matching engine."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.security import get_current_active_user
from app.models.user import User
from app.models.matching import Match, MatchStatus, MatchLineDetail
from app.models.balance import Balance, BalanceType
from services.matching_service import MatchingService
from api.schemas.matching import (
    MatchResponse,
    MatchReview,
    MatchingRequest,
    MatchingResult,
    MatchResult,
    BalanceResponse,
)

router = APIRouter()


@router.get("/matches", response_model=List[MatchResponse])
async def list_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    invoice_id: Optional[UUID] = None,
    dn_id: Optional[UUID] = None,
    po_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all matches with pagination."""
    query = db.query(Match).options(joinedload(Match.line_details))

    if invoice_id:
        query = query.filter(Match.invoice_id == invoice_id)
    if dn_id:
        query = query.filter(Match.dn_id == dn_id)
    if po_id:
        query = query.filter(Match.po_id == po_id)
    if status:
        query = query.filter(Match.status == status)

    total = query.count()
    matches = (
        query.order_by(Match.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return matches


@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a match by ID."""
    match = (
        db.query(Match)
        .options(joinedload(Match.line_details))
        .filter(Match.id == match_id)
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    return match


@router.post("/match-invoice", response_model=MatchingResult)
async def match_invoice(
    request: MatchingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Match an invoice against purchase orders and delivery notes."""
    if not request.invoice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice ID is required",
        )

    matching_service = MatchingService(db)
    result = matching_service.match_invoice(request.invoice_id)

    return result


@router.post("/match-delivery-note", response_model=MatchingResult)
async def match_delivery_note(
    request: MatchingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Match a delivery note against purchase orders."""
    if not request.dn_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery note ID is required",
        )

    matching_service = MatchingService(db)
    result = matching_service.match_delivery_note(request.dn_id)

    return result


@router.post("/match-all", response_model=MatchingResult)
async def match_all(
    request: MatchingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Perform complete 3-way matching for an invoice."""
    if not request.invoice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice ID is required",
        )

    matching_service = MatchingService(db)
    result = matching_service.perform_three_way_match(request.invoice_id)

    return result


@router.post("/matches/{match_id}/review", response_model=MatchResponse)
async def review_match(
    match_id: UUID,
    review: MatchReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Review and update a match status."""
    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if review.status not in [MatchStatus.CONFIRMED.value, MatchStatus.REJECTED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'confirmed' or 'rejected'",
        )

    match.status = review.status
    match.reviewed_by = current_user.id
    match.reviewed_at = datetime.utcnow().isoformat()
    match.review_notes = review.notes

    # Update decision based on status
    if review.status == MatchStatus.CONFIRMED.value:
        match.decision = "APPROVED"
    else:
        match.decision = "DISPUTED"

    db.commit()
    db.refresh(match)

    return match


@router.get("/balances", response_model=List[BalanceResponse])
async def list_balances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_type: Optional[str] = None,
    po_id: Optional[UUID] = None,
    is_settled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all balances with pagination."""
    query = db.query(Balance)

    if document_type:
        query = query.filter(Balance.document_type == document_type)
    if po_id:
        query = query.filter(Balance.po_id == po_id)
    if is_settled is not None:
        query = query.filter(Balance.is_settled == is_settled)

    total = query.count()
    balances = (
        query.order_by(Balance.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return balances


@router.get("/balances/{balance_id}", response_model=BalanceResponse)
async def get_balance(
    balance_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a balance by ID."""
    balance = db.query(Balance).filter(Balance.id == balance_id).first()

    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found",
        )

    return balance
