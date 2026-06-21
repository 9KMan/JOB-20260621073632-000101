// src/api/routes/matches.py
from typing import Annotated
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models.user import User
from src.models.match import Match, MatchStatus, MatchDecision
from src.models.invoice import Invoice
from src.models.delivery_note import DeliveryNote
from src.models.purchase_order import PurchaseOrder
from src.api.routes.auth import get_current_user
from src.api.schemas.match import (
    MatchResponse,
    MatchListResponse,
    MatchReviewRequest,
    MatchSummary
)
from src.services.matching.engine import MatchingEngine

router = APIRouter(prefix="/matches", tags=["Matching"])


@router.post("/match-invoice/{invoice_id}", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def match_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Match an invoice against open purchase orders."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.line_items)
    ).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    engine = MatchingEngine(db)
    match_result = engine.match_invoice_to_po(invoice)
    
    return match_result


@router.post("/match-delivery-note/{dn_id}", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def match_delivery_note(
    dn_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Match a delivery note against open purchase orders."""
    delivery_note = db.query(DeliveryNote).options(
        joinedload(DeliveryNote.line_items)
    ).filter(DeliveryNote.id == dn_id).first()
    
    if not delivery_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found"
        )
    
    engine = MatchingEngine(db)
    match_result = engine.match_dn_to_po(delivery_note)
    
    return match_result


@router.post("/match-three-way/{invoice_id}/{dn_id}", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def match_three_way(
    invoice_id: UUID,
    dn_id: UUID,
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform three-way matching between invoice, delivery note, and PO."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.line_items)
    ).filter(Invoice.id == invoice_id).first()
    
    delivery_note = db.query(DeliveryNote).options(
        joinedload(DeliveryNote.line_items)
    ).filter(DeliveryNote.id == dn_id).first()
    
    purchase_order = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.line_items)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not all([invoice, delivery_note, purchase_order]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more documents not found"
        )
    
    engine = MatchingEngine(db)
    match_result = engine.perform_three_way_match(invoice, delivery_note, purchase_order)
    
    return match_result


@router.get("/", response_model=MatchListResponse)
def list_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    invoice_id: UUID | None = None,
    delivery_note_id: UUID | None = None,
    purchase_order_id: UUID | None = None,
    status_filter: MatchStatus | None = None
):
    """List all matches with pagination."""
    query = db.query(Match)
    
    if invoice_id:
        query = query.filter(Match.invoice_id == invoice_id)
    if delivery_note_id:
        query = query.filter(Match.delivery_note_id == delivery_note_id)
    if purchase_order_id:
        query = query.filter(Match.purchase_order_id == purchase_order_id)
    if status_filter:
        query = query.filter(Match.status == status_filter)
    
    total = query.count()
    items = query.order_by(Match.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return MatchListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a match by ID."""
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    return match


@router.patch("/{match_id}/review", response_model=MatchResponse)
def review_match(
    match_id: UUID,
    review_data: MatchReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review and update match decision."""
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    if match.status == MatchStatus.AUTO_APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot review an auto-approved match"
        )
    
    match.status = MatchStatus.CONFIRMED if review_data.decision != MatchDecision.DISPUTE else MatchStatus.REJECTED
    match.decision = review_data.decision
    match.reviewed_by = current_user.id
    match.reviewed_at = datetime.utcnow()
    match.review_notes = review_data.notes
    match.updated_by = current_user.id
    
    db.commit()
    db.refresh(match)
    
    return match


@router.get("/summary/invoice/{invoice_id}", response_model=MatchSummary)
def get_invoice_match_summary(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get match summary for an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    matches = db.query(Match).filter(Match.invoice_id == invoice_id).all()
    
    auto_approved = sum(1 for m in matches if m.status == MatchStatus.AUTO_APPROVED)
    pending_review = sum(1 for m in matches if m.status == MatchStatus.PENDING)
    rejected = sum(1 for m in matches if m.status == MatchStatus.REJECTED)
    
    return MatchSummary(
        document_type="INVOICE",
        document_id=invoice_id,
        document_number=invoice.invoice_number,
        total_matches=len(matches),
        auto_approved=auto_approved,
        pending_review=pending_review,
        rejected=rejected
    )


@router.get("/summary/purchase-order/{po_id}", response_model=MatchSummary)
def get_po_match_summary(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get match summary for a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    
    matches = db.query(Match).filter(Match.purchase_order_id == po_id).all()
    
    auto_approved = sum(1 for m in matches if m.status == MatchStatus.AUTO_APPROVED)
    pending_review = sum(1 for m in matches if m.status == MatchStatus.PENDING)
    rejected = sum(1 for m in matches if m.status == MatchStatus.REJECTED)
    
    return MatchSummary(
        document_type="PURCHASE_ORDER",
        document_id=po_id,
        document_number=po.po_number,
        total_matches=len(matches),
        auto_approved=auto_approved,
        pending_review=pending_review,
        rejected=rejected
    )
