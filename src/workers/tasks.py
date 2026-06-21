// src/workers/tasks.py
"""Background tasks for matching operations."""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db_context
from src.models.document import Document, DocumentType
from src.models.matching import MatchResult, MatchStatus
from src.services.matching_service import MatchingService
from src.services.balance_service import BalanceService
from src.services.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class MatchingTask:
    """Background task for processing matching operations."""

    def __init__(self):
        self.matching_service: Optional[MatchingService] = None
        self.balance_service: Optional[BalanceService] = None
        self.decision_engine = DecisionEngine()

    async def process_pending_matches(self) -> dict:
        """
        Process all pending match requests.
        
        This can be run as a scheduled background job.
        """
        async with get_db_context() as db:
            # Find documents that need matching
            result = await db.execute(
                select(Document)
                .where(Document.document_type == DocumentType.INVOICE.value)
                .where(Document.status == "SUBMITTED")
            )
            invoices = list(result.scalars().all())

            processed = 0
            failed = 0

            for invoice in invoices:
                try:
                    # Find matching PO
                    po_result = await db.execute(
                        select(Document)
                        .where(Document.document_type == DocumentType.PURCHASE_ORDER.value)
                        .where(Document.supplier_id == invoice.supplier_id)
                        .where(Document.status == "APPROVED")
                    )
                    po = po_result.scalar_one_or_none()

                    if po:
                        self.matching_service = MatchingService(db)
                        self.balance_service = BalanceService(db)

                        match_results = await self.matching_service.perform_3way_match(
                            invoice=invoice,
                            delivery_note=None,
                            purchase_order=po
                        )

                        decision = self.decision_engine.determine_decision(
                            score=match_results.overall_score,
                            has_warnings=match_results.has_warnings,
                            balance_status=match_results.balance_status
                        )

                        await self.matching_service.save_match_result(
                            invoice_id=invoice.id,
                            delivery_note_id=None,
                            purchase_order_id=po.id,
                            match_results=match_results,
                            decision=decision
                        )

                        # Update document status
                        invoice.status = "MATCHED" if decision.status == "AUTO_APPROVED" else "SUBMITTED"

                        processed += 1
                        logger.info(f"Processed match for invoice {invoice.id}")

                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to process invoice {invoice.id}: {e}")

            return {
                "processed": processed,
                "failed": failed,
                "timestamp": datetime.utcnow()
            }

    async def reconcile_old_matches(self, days: int = 30) -> dict:
        """
        Reconcile balances for old matches that need attention.
        
        Args:
            days: Number of days to look back
        """
        async with get_db_context() as db:
            self.balance_service = BalanceService(db)

            result = await db.execute(
                select(MatchResult)
                .where(MatchResult.status == MatchStatus.PENDING_REVIEW)
            )
            pending_matches = list(result.scalars().all())

            reconciled = 0

            for match in pending_matches:
                try:
                    # Get balance entries
                    invoice_balance = await self.balance_service.get_document_balance(
                        UUID(match.invoice_id)
                    )
                    po_balance = await self.balance_service.get_document_balance(
                        UUID(match.purchase_order_id)
                    )

                    # Check if they can be reconciled
                    if invoice_balance and po_balance:
                        inv_bal = invoice_balance[0]
                        po_bal = po_balance[0]

                        if inv_bal.balance_amount == po_bal.balance_amount:
                            # Can auto-reconcile
                            await self.balance_service.resolve_balance(
                                document_id=UUID(match.invoice_id),
                                resolution_type="ADJUST",
                                resolution_amount=inv_bal.balance_amount,
                                notes=f"Auto-reconciled on {datetime.utcnow().isoformat()}"
                            )
                            reconciled += 1

                except Exception as e:
                    logger.error(f"Failed to reconcile match {match.id}: {e}")

            return {
                "reconciled": reconciled,
                "total_pending": len(pending_matches),
                "timestamp": datetime.utcnow()
            }


async def run_matching_task():
    """Entry point for running matching tasks."""
    task = MatchingTask()
    result = await task.process_pending_matches()
    logger.info(f"Matching task completed: {result}")
    return result


async def run_reconciliation_task(days: int = 30):
    """Entry point for running reconciliation tasks."""
    task = MatchingTask()
    result = await task.reconcile_old_matches(days=days)
    logger.info(f"Reconciliation task completed: {result}")
    return result
