// src/api/routes/matches.py
"""Matching API routes for 3-way matching."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.deps import DBSession, CurrentUser
from models.match import Match, MatchConfirmation, MatchDecision, MatchStatus, MatchType
from models.balance import BalanceLedger, BalanceStatus, BalanceType
from models.user import User
from services.matching.layer1_anchor import Layer1AnchorService
from services.matching.layer2_cascade import Layer2CascadeService
from services.matching.layer3_balance import Layer3BalanceService
from services.matching.decision_engine import DecisionEngine

router = APIRouter()


# Pydantic Schemas
class MatchResponse(BaseModel):
    """Schema for Match response."""

    id: str
    match_type: str
    status: str
    decision: Optional[str]
    purchase_order_id: Optional[str]
    invoice_id: Optional[str]
    delivery_note_id: Optional[str]
    total_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    po_amount: Optional[Decimal]
    invoice_amount: Optional[Decimal]
    delivery_amount: Optional[Decimal]
    variance_amount: Decimal
    variance_reasons: Optional[List[str]]
    notes: Optional[str]
    created_at: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Schema for Match list response."""

    items: List[MatchResponse]
    total: int
    page: int
    page_size: int


class MatchConfirmRequest(BaseModel):
    """Schema for confirming/rejecting a match."""

    is_confirmed: bool
    notes: Optional[str] = None


class MatchReviewRequest(BaseModel):
    """Schema for reviewing a match decision."""

    decision: str  # AUTO_APPROVE, HUMAN_REVIEW, or DISPUTE
    notes: Optional[str] = None


class MatchTriggerRequest(BaseModel):
    """Schema for triggering a match."""

    document_type: str  # PO, Invoice, or DN
    document_id: str


class BalanceLedgerResponse(BaseModel):
    """Schema for Balance Ledger response."""

    id: str
    balance_type: str
    status: str
    document_type: str
    document_id: str
    document_number: str
    line_reference: Optional[str]
    original_amount: Decimal
    matched_amount: Decimal
    balance_amount: Decimal
    original_quantity: Decimal
    matched_quantity: Decimal
    balance_quantity: Decimal
    document_date: date
    created_at: str

    class Config:
        from_attributes = True


class MatchingResult(BaseModel):
    """Schema for matching result."""

    matches: List[MatchResponse]
    balances: List[BalanceLedgerResponse]
    summary: dict


@router.post("/trigger", response_model=MatchingResult)
async def trigger_matching(
    request: MatchTriggerRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> dict:
    """
    Trigger matching for a document through all 3 layers.
    
    Layer 1: Anchoring - Match document against POs by supplier and PO number
    Layer 2: Cascade - Match invoice ↔ PO, DN ↔ PO, invoice ↔ DN
    Layer 3: Balance - Track and resolve partial matches
    """
    doc_id = uuid.UUID(request.document_id)
    
    # Execute matching pipeline
    layer1 = Layer1AnchorService(db)
    layer2 = Layer2CascadeService(db)
    layer3 = Layer3BalanceService(db)
    decision_engine = DecisionEngine(db)
    
    # Layer 1: Anchor document to PO
    anchor_result = await layer1.anchor_document(request.document_type, doc_id)
    
    # Layer 2: Cascade matching
    cascade_results = await layer2.perform_cascade_matching(request.document_type, doc_id)
    
    # Layer 3: Balance resolution
    balance_results = await layer3.resolve_balances(request.document_type, doc_id)
    
    # Get all matches for this document
    match_query = select(Match).where(
        (Match.purchase_order_id == doc_id) |
        (Match.invoice_id == doc_id) |
        (Match.delivery_note_id == doc_id)
    )
    result = await db.execute(match_query.options(
        selectinload(Match.purchase_order),
        selectinload(Match.invoice),
        selectinload(Match.delivery_note),
    ))
    matches = result.scalars().all()
    
    # Get balances
    balance_query = select(BalanceLedger).where(BalanceLedger.document_id == doc_id)
    balance_result = await db.execute(balance_query)
    balances = balance_result.scalars().all()
    
    # Apply decision engine to pending matches
    decisions = []
    for match in matches:
        if match.status == MatchStatus.PENDING.value:
            decision = await decision_engine.make_decision(match)
            match.decision = decision.value
            if decision == MatchDecision.AUTO_APPROVE:
                match.status = MatchStatus.CONFIRMED.value
            decisions.append(decision.value)
    
    await db.commit()
    
    # Build summary
    summary = {
        "document_type": request.document_type,
        "document_id": str(doc_id),
        "anchor_found": anchor_result is not None,
        "matches_created": len(cascade_results),
        "balances_updated": len(balance_results),
        "decisions": decisions,
    }
    
    return {
        "matches": matches,
        "balances": balances,
        "summary": summary,
    }


@router.get("", response_model=MatchListResponse)
async def list_matches(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    match_type: Optional[str] = None,
    status: Optional[str] = None,
    decision: Optional[str] = None,
    supplier_code: Optional[str] = None,
) -> dict:
    """List Matches with pagination and filters."""
    query = select(Match)

    if match_type:
        query = query.where(Match.match_type == match_type)
    if status:
        query = query.where(Match.status == status)
    if decision:
        query = query.where(Match.decision == decision)

    # Apply filters
    if supplier_code:
        query = query.join(Match.purchase_order).where(
            Match.purchase_order.has(supplier_code=supplier_code)
        )

    # Get total count
    count_result = await db.execute(select(Match.id))
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.options(
        selectinload(Match.purchase_order),
        selectinload(Match.invoice),
        selectinload(Match.delivery_note),
    )
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Match.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> Match:
    """Get a Match by ID."""
    result = await db.execute(
        select(Match)
        .options(
            selectinload(Match.purchase_order).selectinload(PurchaseOrder),
            selectinload(Match.invoice),
            selectinload(Match.delivery_note),
            selectinload(Match.confirmations),
        )
        .where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    return match


@router.patch("/{match_id}/review", response_model=MatchResponse)
async def review_match(
    match_id: uuid.UUID,
    review: MatchReviewRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> Match:
    """Review and update a match decision."""
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Update decision
    match.decision = review.decision
    match.notes = review.notes
    match.reviewed_by = current_user.id
    match.reviewed_at = datetime.utcnow()

    # Update status based on decision
    if review.decision == MatchDecision.AUTO_APPROVE.value:
        match.status = MatchStatus.CONFIRMED.value
    elif review.decision == MatchDecision.DISPUTE.value:
        match.status = MatchStatus.DISPUTED.value

    await db.commit()
    await db.refresh(match)

    return match


@router.post("/{match_id}/confirm", response_model=MatchResponse)
async def confirm_match(
    match_id: uuid.UUID,
    confirmation: MatchConfirmRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> Match:
    """Confirm or reject a match (for learning loop)."""
    result = await db.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Create confirmation record
    confirm_record = MatchConfirmation(
        match_id=match.id,
        document_type_1=match.match_type.split("_")[0] if "_" in match.match_type else match.match_type,
        document_id_1=match.purchase_order_id or match.invoice_id or match.delivery_note_id,
        document_type_2=match.match_type.split("_")[-1] if "_" in match.match_type else "",
        document_id_2=match.invoice_id or match.delivery_note_id or match.purchase_order_id,
        is_confirmed=confirmation.is_confirmed,
        confirmed_by=current_user.id,
        confirmation_notes=confirmation.notes,
    )
    db.add(confirm_record)

    # Update match status
    if confirmation.is_confirmed:
        match.status = MatchStatus.CONFIRMED.value
        match.decision = MatchDecision.AUTO_APPROVE.value
    else:
        match.status = MatchStatus.REJECTED.value

    await db.commit()
    await db.refresh(match)

    return match


@router.get("/balances", response_model=List[BalanceLedgerResponse])
async def list_balances(
    db: DBSession,
    current_user: CurrentUser,
    balance_type: Optional[str] = None,
    status: Optional[str] = None,
    document_number: Optional[str] = None,
) -> List[BalanceLedger]:
    """List balance ledger entries."""
    query = select(BalanceLedger)

    if balance_type:
        query = query.where(BalanceLedger.balance_type == balance_type)
    if status:
        query = query.where(BalanceLedger.status == status)
    if document_number:
        query = query.where(BalanceLedger.document_number.ilike(f"%{document_number}%"))

    query = query.order_by(BalanceLedger.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


# Import at module level for circular dependency
from models.purchase_order import PurchaseOrder
