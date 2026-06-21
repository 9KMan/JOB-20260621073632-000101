# api/v1/matching.py
"""Matching engine trigger and decision endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import MatchTriggerSchema, MatchingResultSchema
from core.database import DbSession
from core.config import settings
from models import Invoice, InvoiceLine
from models.enums import InvoiceStatus, DecisionType, MatchingStatus
from services.anchoring import AnchoringService
from services.cascade import CascadeService
from services.scoring import ScoringService

router = APIRouter()


@router.post(
    "/trigger",
    response_model=MatchingResultSchema,
    summary="Trigger matching for an invoice",
    description="Run the matching engine for a single invoice.",
)
async def trigger_matching(
    trigger_data: MatchTriggerSchema,
    session: DbSession,
) -> dict:
    """Trigger the matching engine for an invoice."""
    # Get invoice
    result = await session.execute(
        select(Invoice).where(Invoice.id == trigger_data.invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {trigger_data.invoice_id} not found",
        )

    # Check if already matched (unless force rematch)
    if invoice.status == InvoiceStatus.MATCHED.value and not trigger_data.force_rematch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice is already matched. Use force_rematch to rematch.",
        )

    # Update status to processing
    invoice.status = InvoiceStatus.PROCESSING.value
    await session.commit()

    try:
        # Run matching layers
        # Layer 1: PO Anchoring
        anchoring_service = AnchoringService(session)
        await anchoring_service.process_invoice(invoice)

        # Layer 2: Cascade matching
        cascade_service = CascadeService(session)
        await cascade_service.process_invoice(invoice)

        # Calculate final score
        scoring_service = ScoringService(session)
        decision = await scoring_service.calculate_decision(invoice)

        # Update invoice with results
        invoice.status = InvoiceStatus.MATCHED.value
        invoice.matched_at = datetime.now(timezone.utc)
        invoice.match_confidence = decision["confidence"]
        invoice.decision_type = decision["decision_type"]

        await session.commit()
        await session.refresh(invoice)

        # Build response
        matched_lines = sum(
            1 for line in invoice.lines if line.match_status == "matched"
        )
        total_lines = len(invoice.lines)
        matched_amount = sum(
            line.line_amount for line in invoice.lines if line.match_status == "matched"
        )

        return {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "decision_type": decision["decision_type"],
            "match_confidence": decision["confidence"],
            "matched_lines": matched_lines,
            "total_lines": total_lines,
            "matched_amount": matched_amount,
            "total_amount": invoice.total_amount,
            "exceptions": decision.get("exceptions", []),
            "processed_at": invoice.matched_at,
        }

    except Exception as e:
        # Rollback on error
        invoice.status = InvoiceStatus.EXCEPTION.value
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {str(e)}",
        )


@router.get(
    "/decision/{invoice_id}",
    summary="Get matching decision for an invoice",
    description="Retrieve the matching decision and details for a matched invoice.",
)
async def get_decision(
    invoice_id: str,
    session: DbSession,
) -> dict:
    """Get matching decision for an invoice."""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    if invoice.status != InvoiceStatus.MATCHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice has not been matched yet",
        )

    # Build decision details
    scoring_service = ScoringService(session)
    decision = await scoring_service.get_decision_details(invoice)

    return decision


@router.post(
    "/batch",
    summary="Trigger batch matching",
    description="Run matching for multiple invoices.",
)
async def trigger_batch_matching(
    invoice_ids: list[str],
    session: DbSession,
) -> dict:
    """Trigger batch matching for multiple invoices."""
    results = []
    errors = []

    for invoice_id in invoice_ids:
        try:
            result = await trigger_matching(
                MatchTriggerSchema(invoice_id=invoice_id, force_rematch=False),
                session,
            )
            results.append(result)
        except Exception as e:
            errors.append({"invoice_id": invoice_id, "error": str(e)})

    return {
        "total": len(invoice_ids),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
