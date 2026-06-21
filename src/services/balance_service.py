// src/services/balance_service.py
"""Balance tracking service for partial matches."""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.balance import BalanceLedger, BalanceLedgerEntry
from src.models.delivery_note import DeliveryNote
from src.models.invoice import Invoice
from src.models.purchase_order import PurchaseOrder

logger = logging.getLogger(__name__)


class BalanceService:
    """Service for tracking document balances."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_balance_entry(
        self,
        document_type: str,
        document_id: UUID,
        document_number: str,
        original_amount: Decimal,
    ) -> BalanceLedger:
        """Create initial balance entry for a document."""
        balance = BalanceLedger(
            document_type=document_type,
            document_id=document_id,
            document_number=document_number,
            original_amount=original_amount,
            matched_amount=Decimal("0.00"),
            pending_amount=original_amount,
            balance_status="OPEN",
        )
        self.db.add(balance)
        await self.db.flush()
        await self.db.refresh(balance)
        return balance
    
    async def record_match(
        self,
        document_type: str,
        document_id: UUID,
        match_id: UUID,
        match_amount: Decimal,
        reference_type: str,
        reference_id: UUID,
        reference_number: str,
    ) -> Optional[BalanceLedger]:
        """Record a match against a document's balance."""
        result = await self.db.execute(
            select(BalanceLedger).where(
                BalanceLedger.document_type == document_type,
                BalanceLedger.document_id == document_id,
                BalanceLedger.is_deleted == False,
            )
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            logger.warning(f"No balance found for {document_type}:{document_id}")
            return None
        
        new_matched = balance.matched_amount + match_amount
        new_pending = balance.original_amount - new_matched
        
        balance.matched_amount = new_matched
        balance.pending_amount = new_pending
        
        if new_pending <= Decimal("0.00"):
            balance.balance_status = "CLOSED"
            balance.closed_at = datetime.utcnow()
        
        entry = BalanceLedgerEntry(
            balance_ledger_id=balance.id,
            match_id=match_id,
            entry_type="MATCH",
            amount=match_amount,
            balance_after=new_pending,
            reference_document_type=reference_type,
            reference_document_id=reference_id,
            reference_document_number=reference_number,
        )
        self.db.add(entry)
        
        await self.db.flush()
        await self.db.refresh(balance)
        return balance
    
    async def reverse_match(
        self,
        document_type: str,
        document_id: UUID,
        match_id: UUID,
        amount: Decimal,
    ) -> Optional[BalanceLedger]:
        """Reverse a match and restore the balance."""
        result = await self.db.execute(
            select(BalanceLedger).where(
                BalanceLedger.document_type == document_type,
                BalanceLedger.document_id == document_id,
                BalanceLedger.is_deleted == False,
            )
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            return None
        
        new_matched = max(Decimal("0.00"), balance.matched_amount - amount)
        new_pending = balance.original_amount - new_matched
        
        balance.matched_amount = new_matched
        balance.pending_amount = new_pending
        balance.balance_status = "PARTIAL" if new_pending > Decimal("0.00") else "CLOSED"
        
        if balance.balance_status == "CLOSED":
            balance.closed_at = datetime.utcnow()
        
        entry = BalanceLedgerEntry(
            balance_ledger_id=balance.id,
            match_id=match_id,
            entry_type="REVERSE",
            amount=amount,
            balance_after=new_pending,
        )
        self.db.add(entry)
        
        await self.db.flush()
        await self.db.refresh(balance)
        return balance
    
    async def get_balance_for_document(
        self,
        document_type: str,
        document_id: UUID,
    ) -> Optional[BalanceLedger]:
        """Get balance entry for a document."""
        result = await self.db.execute(
            select(BalanceLedger)
            .where(
                BalanceLedger.document_type == document_type,
                BalanceLedger.document_id == document_id,
                BalanceLedger.is_deleted == False,
            )
            .options(selectinload(BalanceLedger.entries))
        )
        return result.scalar_one_or_none()
    
    async def get_open_balances(
        self,
        document_type: Optional[str] = None,
        include_partial: bool = True,
    ) -> list[BalanceLedger]:
        """Get all open balances, optionally filtered by document type."""
        query = select(BalanceLedger).where(BalanceLedger.is_deleted == False)
        
        if document_type:
            query = query.where(BalanceLedger.document_type == document_type)
        
        if include_partial:
            query = query.where(BalanceLedger.balance_status.in_(["OPEN", "PARTIAL"]))
        else:
            query = query.where(BalanceLedger.balance_status == "OPEN")
        
        query = query.order_by(BalanceLedger.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_balance_summary(self) -> dict:
        """Get summary of all balances."""
        balances = await self.get_open_balances(include_partial=True)
        
        total_original = sum(b.original_amount for b in balances)
        total_matched = sum(b.matched_amount for b in balances)
        total_pending = sum(b.pending_amount for b in balances)
        
        open_count = sum(1 for b in balances if b.balance_status == "OPEN")
        partial_count = sum(1 for b in balances if b.balance_status == "PARTIAL")
        
        return {
            "total_documents": len(balances),
            "open_documents": open_count,
            "partial_documents": partial_count,
            "total_original_amount": total_original,
            "total_matched_amount": total_matched,
            "total_pending_amount": total_pending,
            "match_percentage": (
                (total_matched / total_original * 100).quantize(Decimal("0.01"))
                if total_original > 0 else Decimal("0.00")
            ),
        }
