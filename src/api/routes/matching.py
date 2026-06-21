// src/api/routes/matching.py
"""Matching endpoints for 3-way matching operations."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.database import get_db
from src.api.schemas.matching import (
    MatchRequest,
    MatchResponse,
    MatchResultResponse,
    BalanceResponse,
    BatchMatchRequest,
    BatchMatchResponse,
    MatchStatusEnum,
)
from src.models.document import Document, DocumentLine
from src.models.matching import MatchResult, BalanceLedger, CrossReference
from src.services.matching_service import MatchingService
from src.services.balance_service import BalanceService
from src.services.decision_engine import DecisionEngine

router = APIRouter(prefix="/matching", tags=["Matching"])


def get_matching_service(db: AsyncSession = Depends(get_db)) -> MatchingService:
    """Dependency to get matching service instance."""
    return MatchingService(db)


def get_balance_service(db: AsyncSession = Depends(get_db)) -> BalanceService:
    """Dependency to get balance service instance."""
    return BalanceService(db)


def get_decision_engine() -> DecisionEngine:
    """Dependency to get decision engine instance."""
    return DecisionEngine()


@router.post("/match", response_model=MatchResponse)
async def match_documents(
    request: MatchRequest,
    matching_service: MatchingService = Depends(get_matching_service),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
) -> MatchResponse:
    """
    Perform 3-way matching between Invoice, Delivery Note, and Purchase Order.
    
    Layer 1: Anchoring - Match against Purchase Order first
    Layer 2: Cascade Matching - Match invoice↔PO, DN↔PO, invoice↔DN
    Layer 3: Balance Resolution - Track partial matches and balances
    """
    # Fetch documents
    invoice = await matching_service.get_document(request.invoice_id)
    delivery_note = None
    if request.delivery_note_id:
        delivery_note = await matching_service.get_document(request.delivery_note_id)
    purchase_order = await matching_service.get_document(request.purchase_order_id)

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase Order is required for matching"
        )

    # Perform 3-way matching
    match_results = await matching_service.perform_3way_match(
        invoice=invoice,
        delivery_note=delivery_note,
        purchase_order=purchase_order
    )

    # Determine decision
    overall_score = match_results.overall_score
    decision = decision_engine.determine_decision(
        score=overall_score,
        has_warnings=match_results.has_warnings,
        balance_status=match_results.balance_status
    )

    # Save match result
    saved_result = await matching_service.save_match_result(
        invoice_id=request.invoice_id,
        delivery_note_id=request.delivery_note_id,
        purchase_order_id=request.purchase_order_id,
        match_results=match_results,
        decision=decision
    )

    return MatchResponse(
        match_id=saved_result.id,
        invoice_id=request.invoice_id,
        delivery_note_id=request.delivery_note_id,
        purchase_order_id=request.purchase_order_id,
        status=MatchStatusEnum(decision.status),
        overall_score=overall_score,
        line_matches=match_results.line_matches,
        amount_variance=match_results.amount_variance,
        quantity_variance=match_results.quantity_variance,
        date_variance=match_results.date_variance,
        balance_status=match_results.balance_status,
        warnings=match_results.warnings,
        decision=decision,
        created_at=saved_result.created_at
    )


@router.post("/batch", response_model=BatchMatchResponse)
async def batch_match_documents(
    request: BatchMatchRequest,
    matching_service: MatchingService = Depends(get_matching_service),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
) -> BatchMatchResponse:
    """Perform batch matching for multiple document sets."""
    results = []
    auto_approved = 0
    pending_review = 0
    rejected = 0

    for match_request in request.matches:
        try:
            invoice = await matching_service.get_document(match_request.invoice_id)
            delivery_note = None
            if match_request.delivery_note_id:
                delivery_note = await matching_service.get_document(match_request.delivery_note_id)
            purchase_order = await matching_service.get_document(match_request.purchase_order_id)

            if not purchase_order:
                results.append({
                    "request": match_request.model_dump(),
                    "error": "Purchase Order not found"
                })
                continue

            match_results = await matching_service.perform_3way_match(
                invoice=invoice,
                delivery_note=delivery_note,
                purchase_order=purchase_order
            )

            decision = decision_engine.determine_decision(
                score=match_results.overall_score,
                has_warnings=match_results.has_warnings,
                balance_status=match_results.balance_status
            )

            saved_result = await matching_service.save_match_result(
                invoice_id=match_request.invoice_id,
                delivery_note_id=match_request.delivery_note_id,
                purchase_order_id=match_request.purchase_order_id,
                match_results=match_results,
                decision=decision
            )

            if decision.status == "AUTO_APPROVED":
                auto_approved += 1
            elif decision.status == "PENDING_REVIEW":
                pending_review += 1
            else:
                rejected += 1

            results.append({
                "match_id": str(saved_result.id),
                "status": decision.status,
                "score": match_results.overall_score
            })

        except Exception as e:
            results.append({
                "request": match_request.model_dump(),
                "error": str(e)
            })

    return BatchMatchResponse(
        total=len(request.matches),
        successful=len([r for r in results if "match_id" in r]),
        failed=len([r for r in results if "error" in r]),
        auto_approved=auto_approved,
        pending_review=pending_review,
        rejected=rejected,
        results=results
    )


@router.get("/results/{match_id}", response_model=MatchResultResponse)
async def get_match_result(
    match_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> MatchResultResponse:
    """Get a specific match result."""
    result = await db.execute(
        select(MatchResult)
        .options(
            selectinload(MatchResult.line_matches),
            selectinload(MatchResult.cross_references)
        )
        .where(MatchResult.id == match_id)
    )
    match_result = result.scalar_one_or_none()

    if not match_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match result with ID {match_id} not found"
        )

    return MatchResultResponse.model_validate(match_result)


@router.get("/results", response_model=list[MatchResultResponse])
async def list_match_results(
    status_filter: Optional[MatchStatusEnum] = Query(None, alias="status"),
    invoice_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> list[MatchResultResponse]:
    """List match results with optional filters."""
    query = select(MatchResult).options(
        selectinload(MatchResult.line_matches),
        selectinload(MatchResult.cross_references)
    )

    if status_filter:
        query = query.where(MatchResult.status == status_filter.value)
    if invoice_id:
        query = query.where(MatchResult.invoice_id == invoice_id)

    query = query.offset(skip).limit(limit).order_by(MatchResult.created_at.desc())

    result = await db.execute(query)
    return [MatchResultResponse.model_validate(mr) for mr in result.scalars().all()]


@router.get("/balance/{document_id}", response_model=list[BalanceResponse])
async def get_document_balance(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> list[BalanceResponse]:
    """Get balance ledger entries for a document."""
    balance_service = BalanceService(db)
    balances = await balance_service.get_document_balance(document_id)
    return [BalanceResponse.model_validate(b) for b in balances]


@router.post("/balance/resolve", response_model=dict)
async def resolve_balance(
    document_id: UUID,
    resolution_type: str,
    resolution_amount: float,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Resolve a balance discrepancy."""
    balance_service = BalanceService(db)
    success = await balance_service.resolve_balance(
        document_id=document_id,
        resolution_type=resolution_type,
        resolution_amount=resolution_amount,
        notes=notes
    )
    return {"success": success, "message": f"Balance {resolution_type} processed"}
