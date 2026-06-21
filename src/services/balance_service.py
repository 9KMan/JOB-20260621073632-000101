// src/services/balance_service.py
"""Balance ledger service for tracking partial matches and resolutions."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.balance_ledger import (
    BalanceLedger, BalanceType, BalanceDirection, BalanceStatus
)
from src.models.matching import MatchingRecord


class BalanceService:
    """
    Layer 3: Balance Resolution Service.
    Tracks partial matches and balances across all document types.
    Handles partial shipments, split invoices, and multi-delivery scenarios.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_balance_for_variance(
        self,
        matching_record: MatchingRecord,
        variance_amount: Decimal,
        source_document_type: str = "invoice",
        source_document_id: Optional[UUID] = None
    ) -> BalanceLedger:
        """
        Create a balance entry for a variance discovered during matching.
        Used in Layer 3 to track unmatched amounts.
        """
        if source_document_type == "invoice" and matching_record.invoice_id:
            source_document_id = matching_record.invoice_id
        elif source_document_type == "delivery" and matching_record.delivery_note_id:
            source_document_id = matching_record.delivery_note_id
        
        balance = BalanceLedger(
            balance_type=BalanceType.PARTIAL_MATCH.value,
            direction=BalanceDirection.DEBIT.value,
            status=BalanceStatus.OPEN.value,
            source_document_type=source_document_type,
            source_document_id=source_document_id or matching_record.purchase_order_id,
            original_amount=variance_amount,
            balance_amount=variance_amount,
            currency="USD",
            matching_record_id=matching_record.id,
            notes=f"Variance from {matching_record.match_type} matching"
        )
        
        self.db.add(balance)
        self.db.flush()
        
        return balance

    def create_invoice_balance(
        self,
        invoice_id: UUID,
        amount: Decimal,
        po_id: Optional[UUID] = None
    ) -> BalanceLedger:
        """Create a balance entry for an unmatched invoice amount."""
        balance = BalanceLedger(
            balance_type=BalanceType.INVOICE_BALANCE.value,
            direction=BalanceDirection.DEBIT.value,
            status=BalanceStatus.OPEN.value,
            source_document_type="invoice",
            source_document_id=invoice_id,
            related_document_type="purchase_order" if po_id else None,
            related_document_id=po_id,
            original_amount=amount,
            balance_amount=amount,
            currency="USD"
        )
        
        self.db.add(balance)
        self.db.flush()
        
        return balance

    def create_delivery_balance(
        self,
        delivery_note_id: UUID,
        amount: Decimal,
        po_id: Optional[UUID] = None
    ) -> BalanceLedger:
        """Create a balance entry for an unmatched delivery amount."""
        balance = BalanceLedger(
            balance_type=BalanceType.DELIVERY_BALANCE.value,
            direction=BalanceDirection.CREDIT.value,
            status=BalanceStatus.OPEN.value,
            source_document_type="delivery_note",
            source_document_id=delivery_note_id,
            related_document_type="purchase_order" if po_id else None,
            related_document_id=po_id,
            original_amount=amount,
            balance_amount=amount,
            currency="USD"
        )
        
        self.db.add(balance)
        self.db.flush()
        
        return balance

    def resolve_balance(
        self,
        balance_id: UUID,
        resolution_type: str,
        resolve_amount: Optional[Decimal] = None,
        user_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        transaction_reference: Optional[str] = None
    ) -> BalanceLedger:
        """Resolve a balance entry."""
        balance = self.db.query(BalanceLedger).filter(
            BalanceLedger.id == balance_id
        ).first()
        
        if not balance:
            raise ValueError(f"Balance {balance_id} not found")
        
        amount_to_resolve = resolve_amount or balance.balance_amount
        
        balance.resolved_amount += amount_to_resolve
        balance.balance_amount -= amount_to_resolve
        balance.resolution_type = resolution_type
        balance.resolved_by_id = user_id
        balance.resolved_at = datetime.utcnow()
        
        if notes:
            balance.resolution_notes = notes
        if transaction_reference:
            balance.transaction_reference = transaction_reference
        
        # Update status based on remaining balance
        if balance.balance_amount <= 0:
            balance.status = BalanceStatus.RESOLVED.value
            balance.balance_amount = Decimal("0.00")
        else:
            balance.status = BalanceStatus.PARTIALLY_RESOLVED.value
        
        self.db.flush()
        return balance

    def write_off_balance(
        self,
        balance_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> BalanceLedger:
        """Write off an unresolved balance."""
        balance = self.db.query(BalanceLedger).filter(
            BalanceLedger.id == balance_id
        ).first()
        
        if not balance:
            raise ValueError(f"Balance {balance_id} not found")
        
        balance.resolved_amount = balance.original_amount
        balance.balance_amount = Decimal("0.00")
        balance.status = BalanceStatus.WRITE_OFF.value
        balance.resolution_type = "write_off"
        balance.resolved_by_id = user_id
        balance.resolved_at = datetime.utcnow()
        
        if notes:
            balance.resolution_notes = notes
        
        self.db.flush()
        return balance

    def dispute_balance(
        self,
        balance_id: UUID,
        notes: Optional[str] = None
    ) -> BalanceLedger:
        """Mark a balance as disputed."""
        balance = self.db.query(BalanceLedger).filter(
            BalanceLedger.id == balance_id
        ).first()
        
        if not balance:
            raise ValueError(f"Balance {balance_id} not found")
        
        balance.status = BalanceStatus.DISPUTED.value
        if notes:
            balance.notes = (balance.notes or "") + f"\nDispute: {notes}"
        
        self.db.flush()
        return balance

    def get_open_balances(
        self,
        document_type: Optional[str] = None,
        document_id: Optional[UUID] = None
    ) -> list[BalanceLedger]:
        """Get all open balances, optionally filtered by document."""
        query = self.db.query(BalanceLedger).filter(
            BalanceLedger.status.in_([
                BalanceStatus.OPEN.value,
                BalanceStatus.PARTIALLY_RESOLVED.value
            ])
        )
        
        if document_type:
            query = query.filter(BalanceLedger.source_document_type == document_type)
        
        if document_id:
            query = query.filter(BalanceLedger.source_document_id == document_id)
        
        return query.order_by(BalanceLedger.created_at.desc()).all()

    def get_balance_summary(self) -> dict:
        """Get summary of all balances."""
        from sqlalchemy import func
        
        # Count by status
        status_counts = self.db.query(
            BalanceLedger.status,
            func.count(BalanceLedger.id)
        ).group_by(BalanceLedger.status).all()
        
        # Sum by status
        amount_sums = self.db.query(
            BalanceLedger.status,
            func.sum(BalanceLedger.balance_amount)
        ).group_by(BalanceLedger.status).all()
        
        status_dict = dict(status_counts)
        amount_dict = dict(amount_sums)
        
        total_open = (
            status_dict.get(BalanceStatus.OPEN.value, 0) +
            status_dict.get(BalanceStatus.PARTIALLY_RESOLVED.value, 0)
        )
        total_resolved = (
            status_dict.get(BalanceStatus.RESOLVED.value, 0) +
            status_dict.get(BalanceStatus.WRITE_OFF.value, 0)
        )
        total_disputed = status_dict.get(BalanceStatus.DISPUTED.value, 0)
        
        open_amount = (
            amount_dict.get(BalanceStatus.OPEN.value, Decimal("0.00")) +
            amount_dict.get(BalanceStatus.PARTIALLY_RESOLVED.value, Decimal("0.00"))
        )
        resolved_amount = (
            amount_dict.get(BalanceStatus.RESOLVED.value, Decimal("0.00")) +
            amount_dict.get(BalanceStatus.WRITE_OFF.value, Decimal("0.00"))
        )
        
        return {
            "total_open": total_open,
            "total_resolved": total_resolved,
            "total_disputed": total_disputed,
            "total_open_amount": float(open_amount or Decimal("0.00")),
            "total_resolved_amount": float(resolved_amount or Decimal("0.00"))
        }

    def get_balances_by_document(
        self,
        document_type: str,
        document_id: UUID
    ) -> list[BalanceLedger]:
        """Get all balances for a specific document."""
        return self.db.query(BalanceLedger).filter(
            BalanceLedger.source_document_type == document_type,
            BalanceLedger.source_document_id == document_id
        ).all()

    def apply_balance_offset(
        self,
        debit_balance_id: UUID,
        credit_balance_id: UUID,
        offset_amount: Decimal,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> tuple[BalanceLedger, BalanceLedger]:
        """
        Apply an offset between a debit and credit balance.
        Common for handling credit notes against invoices.
        """
        debit_balance = self.db.query(BalanceLedger).filter(
            BalanceLedger.id == debit_balance_id
        ).first()
        
        credit_balance = self.db.query(BalanceLedger).filter(
            BalanceLedger.id == credit_balance_id
        ).first()
        
        if not debit_balance or not credit_balance:
            raise ValueError("Both balances must exist")
        
        # Create the offset relationship
        debit_balance.related_document_type = credit_balance.source_document_type
        debit_balance.related_document_id = credit_balance.source_document_id
        
        # Resolve amounts
        debit_balance.resolved_amount += offset_amount
        debit_balance.balance_amount -= offset_amount
        
        credit_balance.resolved_amount += offset_amount
        credit_balance.balance_amount -= offset_amount
        
        # Update statuses
        if debit_balance.balance_amount <= 0:
            debit_balance.status = BalanceStatus.RESOLVED.value
            debit_balance.balance_amount = Decimal("0.00")
        
        if credit_balance.balance_amount <= 0:
            credit_balance.status = BalanceStatus.RESOLVED.value
            credit_balance.balance_amount = Decimal("0.00")
        
        debit_balance.resolution_type = "offset"
        credit_balance.resolution_type = "offset"
        debit_balance.resolved_by_id = user_id
        credit_balance.resolved_by_id = user_id
        debit_balance.resolved_at = datetime.utcnow()
        credit_balance.resolved_at = datetime.utcnow()
        
        if notes:
            debit_balance.resolution_notes = notes
        
        self.db.flush()
        
        return debit_balance, credit_balance
