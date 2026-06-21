// src/api/routes/matches.py
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.models.match import Match, MatchLine, MatchStatus, MatchDecision
from src.models.user import User
from src.api.schemas.match import MatchResponse, MatchConfirmRequest
from src.services.matching_service import MatchingService
from src.dependencies import get_current_active_user

router = APIRouter()


@router.post("/match/{invoice_id}", response_model=List[MatchResponse], status_code=status.HTTP_201_CREATED)
async def match_invoice(
    invoice_id: str,
    delivery_note_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    matching_service = MatchingService(db)
    
    try:
        matches = matching_service.perform_three_way_match(
            invoice_id=invoice_id,
            delivery_note_id=delivery_note_id,
            user_id=str(current_user.id)
        )
        return matches
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[MatchResponse])
async def list_matches(
    skip: int = 0,
    limit: int = 100,
    invoice_id: Optional[str] = None,
    purchase_order_id: Optional[str] = None,
    delivery_note_id: Optional[str] = None,
    status: Optional[MatchStatus] = None,
    decision: Optional[MatchDecision] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Match).options(
        joinedload(Match.lines),
        joinedload(Match.invoice),
        joinedload(Match.purchase_order),
        joinedload(Match.delivery_note)
    )
    
    if invoice_id:
        query = query.filter(Match.invoice_id == invoice_id)
    if purchase_order_id:
        query = query.filter(Match.purchase_order_id == purchase_order_id)
    if delivery_note_id:
        query = query.filter(Match.delivery_note_id == delivery_note_id)
    if status:
        query = query.filter(Match.status == status)
    if decision:
        query = query.filter(Match.decision == decision)
    
    matches = query.offset(skip).limit(limit).all()
    return matches


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).options(
        joinedload(Match.lines),
        joinedload(Match.invoice),
        joinedload(Match.purchase_order),
        joinedload(Match.delivery_note)
    ).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} not found"
        )
    return match


@router.post("/{match_id}/confirm", response_model=MatchResponse)
async def confirm_match(
    match_id: str,
    confirm_data: MatchConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} not found"
        )
    
    if confirm_data.confirm:
        match.status = MatchStatus.CONFIRMED
        match.confirmed_by = current_user.id
        match.confirmed_at = datetime.utcnow()
    else:
        match.status = MatchStatus.REJECTED
        match.decision = MatchDecision.DISPUTE
        match.confirmed_by = current_user.id
        match.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(match)
    return match


@router.post("/auto-match", response_model=List[MatchResponse], status_code=status.HTTP_201_CREATED)
async def auto_match_all_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    matching_service = MatchingService(db)
    matches = matching_service.auto_match_pending_invoices(str(current_user.id))
    return matches
