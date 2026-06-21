// src/services/balance_service.py
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.models import (
    PurchaseOrder,
    Invoice,
    DeliveryNote,
    MatchRecord,
    BalanceRecord,
)
from src.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BalanceService:
    """
    Balance Service - Layer 3 of the matching architecture.
    
    Tracks partial matches and balances across all three document types.
    Handles:
    - Partial shipments
    - Split invoices
    - Multi-delivery scenarios
    """

    def __init__(self, db: Session):
        self.db = db
        self.tolerance_amount = settings.BALANCE_TOLERANCE_AMOUNT
        self.tolerance_percent = settings.BALANCE_TOLERANCE_PERCENT

    def create_balance_records(
        self, match_record: MatchRecord
    ) -> List[BalanceRecord]:
        """
        Create balance records for a match.
        
        Tracks how much of each document has been matched.
        """
        balance_records = []
        
        # Create PO balance record
        if match_record.po_id and match_record.po_amount:
            po_balance = self._create_document_balance(
                match_record=match_record,
                document_type="PO",
                document_id=match_record.po_id,
                original_amount=float(match_record.po_amount),
            )
            balance_records.append(po_balance)
        
        # Create Invoice balance record
        if match_record.invoice_id and match_record.invoice_amount:
            inv_balance = self._create_document_balance(
                match_record=match_record,
                document_type="Invoice",
                document_id=match_record.invoice_id,
                original_amount=float(match_record.invoice_amount),
            )
            balance_records.append(inv_balance)
        
        # Create DN balance record
        if match_record.dn_id and match_record.dn_amount:
            dn_balance = self._create_document_balance(
                match_record=match_record,
                document_type="DN",
                document_id=match_record.dn_id,
                original_amount=float(match_record.dn_amount),
            )
            balance_records.append(dn_balance)
        
        for record in balance_records:
            self.db.add(record)
        
        self.db.flush()
        
        logger.info(
            f"Created {len(balance_records)} balance records for match {match_record.id}"
        )
        
        return balance_records

    def _create_document_balance(
        self,
        match_record: MatchRecord,
        document_type: str,
        document_id: UUID,
        original_amount: float,
    ) -> BalanceRecord:
        """Create a balance record for a single document."""
        # Calculate matched amount from other documents in the match
        matched_amount = self._calculate_matched_amount(
            match_record, document_type
        )
        
        balance_amount = original_amount - matched_amount
        
        # Check if essentially resolved (within tolerance)
        is_resolved = abs(balance_amount) <= self.tolerance_amount
        
        return BalanceRecord(
            match_record_id=match_record.id,
            document_type=document_type,
            document_id=document_id,
            original_amount=original_amount,
            matched_amount=matched_amount,
            balance_amount=balance_amount if not is_resolved else 0,
            is_resolved=is_resolved,
        )

    def _calculate_matched_amount(
        self, match_record: MatchRecord, document_type: str
    ) -> float:
        """Calculate how much of a document has been matched."""
        matched_amount = 0.0
        
        if document_type == "PO":
            # PO is matched by invoice and/or DN
            if match_record.invoice_amount:
                matched_amount += float(match_record.invoice_amount)
            if match_record.dn_amount:
                matched_amount += float(match_record.dn_amount)
            # Cap at PO amount
            if match_record.po_amount:
                matched_amount = min(matched_amount, float(match_record.po_amount))
                
        elif document_type == "Invoice":
            # Invoice is matched by PO
            if match_record.po_amount:
                matched_amount = float(match_record.po_amount)
            # Cap at invoice amount
            if match_record.invoice_amount:
                matched_amount = min(matched_amount, float(match_record.invoice_amount))
                
        elif document_type == "DN":
            # DN is matched by PO
            if match_record.po_amount:
                matched_amount = float(match_record.po_amount)
            # Cap at DN amount
            if match_record.dn_amount:
                matched_amount = min(matched_amount, float(match_record.dn_amount))
        
        return matched_amount

    def update_balance_for_partial_match(
        self,
        document_type: str,
        document_id: UUID,
        match_amount: float,
        match_record_id: UUID,
    ) -> BalanceRecord:
        """
        Update balance record for a partial match.
        
        This is used when a document is matched incrementally.
        """
        balance = self._get_or_create_balance(document_type, document_id)
        
        balance.matched_amount = float(Decimal(str(balance.matched_amount)) + Decimal(str(match_amount)))
        balance.balance_amount = float(
            Decimal(str(balance.original_amount)) - Decimal(str(balance.matched_amount))
        )
        
        # Check if resolved
        if abs(balance.balance_amount) <= self.tolerance_amount:
            balance.is_resolved = True
            balance.resolved_at = datetime.utcnow()
            balance.resolved_by_match_id = match_record_id
        
        self.db.flush()
        
        logger.info(
            f"Updated balance for {document_type} {document_id}: "
            f"matched={balance.matched_amount}, balance={balance.balance_amount}"
        )
        
        return balance

    def _get_or_create_balance(
        self, document_type: str, document_id: UUID
    ) -> BalanceRecord:
        """Get existing balance record or create new one."""
        balance = (
            self.db.query(BalanceRecord)
            .filter(
                BalanceRecord.document_type == document_type,
                BalanceRecord.document_id == document_id,
                BalanceRecord.is_resolved == False,
            )
            .first()
        )
        
        if not balance:
            # Get original amount from document
            original_amount = self._get_document_amount(document_type, document_id)
            balance = BalanceRecord(
                document_type=document_type,
                document_id=document_id,
                original_amount=original_amount,
                matched_amount=0,
                balance_amount=original_amount,
            )
            self.db.add(balance)
            self.db.flush()
        
        return balance

    def _get_document_amount(self, document_type: str, document_id: UUID) -> float:
        """Get the total amount from a document."""
        if document_type == "PO":
            doc = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == document_id).first()
        elif document_type == "Invoice":
            doc = self.db.query(Invoice).filter(Invoice.id == document_id).first()
        elif document_type == "DN":
            doc = self.db.query(DeliveryNote).filter(DeliveryNote.id == document_id).first()
        else:
            return 0.0
        
        if doc:
            return float(doc.total_amount)
        return 0.0

    def get_document_balance(
        self, document_type: str, document_id: UUID
    ) -> Optional[BalanceRecord]:
        """Get current balance for a document."""
        return (
            self.db.query(BalanceRecord)
            .filter(
                BalanceRecord.document_type == document_type,
                BalanceRecord.document_id == document_id,
                BalanceRecord.is_resolved == False,
            )
            .order_by(BalanceRecord.created_at.desc())
            .first()
        )

    def get_unresolved_balances(
        self, document_type: Optional[str] = None, limit: int = 100
    ) -> List[BalanceRecord]:
        """Get all unresolved balance records."""
        query = self.db.query(BalanceRecord).filter(BalanceRecord.is_resolved == False)
        
        if document_type:
            query = query.filter(BalanceRecord.document_type == document_type)
        
        return (
            query.order_by(BalanceRecord.balance_amount.desc())
            .limit(limit)
            .all()
        )

    def resolve_balance(
        self,
        document_type: str,
        document_id: UUID,
        resolution_match_id: UUID,
    ) -> BalanceRecord:
        """
        Manually resolve a balance.
        
        Used when a balance is resolved through manual intervention.
        """
        balance = self._get_or_create_balance(document_type, document_id)
        
        balance.is_resolved = True
        balance.resolved_at = datetime.utcnow()
        balance.resolved_by_match_id = resolution_match_id
        balance.balance_amount = 0
        
        self.db.flush()
        
        logger.info(
            f"Manually resolved balance for {document_type} {document_id} "
            f"via match {resolution_match_id}"
        )
        
        return balance

    def get_balance_summary(self, match_record_id: UUID) -> Dict:
        """Get a summary of balances for a match."""
        balances = (
            self.db.query(BalanceRecord)
            .filter(BalanceRecord.match_record_id == match_record_id)
            .all()
        )
        
        summary = {
            "total_documents": len(balances),
            "total_original": sum(b.original_amount for b in balances),
            "total_matched": sum(b.matched_amount for b in balances),
            "total_balance": sum(b.balance_amount for b in balances),
            "resolved_count": sum(1 for b in balances if b.is_resolved),
            "unresolved_count": sum(1 for b in balances if not b.is_resolved),
            "documents": [
                {
                    "type": b.document_type,
                    "id": str(b.document_id),
                    "original": b.original_amount,
                    "matched": b.matched_amount,
                    "balance": b.balance_amount,
                    "is_resolved": b.is_resolved,
                }
                for b in balances
            ],
        }
        
        return summary

    def close_document_balances(
        self, document_type: str, document_id: UUID
    ) -> None:
        """
        Close all open balances for a document.
        
        Called when a document is fully closed/cancelled.
        """
        balances = (
            self.db.query(BalanceRecord)
            .filter(
                BalanceRecord.document_type == document_type,
                BalanceRecord.document_id == document_id,
                BalanceRecord.is_resolved == False,
            )
            .all()
        )
        
        for balance in balances:
            balance.is_resolved = True
            balance.resolved_at = datetime.utcnow()
            balance.balance_amount = 0
        
        self.db.flush()
        
        logger.info(
            f"Closed {len(balances)} balances for {document_type} {document_id}"
        )
