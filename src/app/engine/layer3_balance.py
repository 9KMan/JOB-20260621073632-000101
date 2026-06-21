// src/app/engine/layer3_balance.py
"""Layer 3: Balance Resolution - Tracks partial matches and balances."""

from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from src.app.models import (
    Invoice, PurchaseOrder, DeliveryNote,
    BalanceLedger, BalanceType, MatchResult
)


class Layer3Balance:
    """
    Layer 3 - Balance Resolution Engine
    
    Tracks partial matches and balances across all three document types
    using a balances ledger. This allows the system to handle:
    - Partial shipments
    - Split invoices
    - Multi-delivery scenarios
    """

    def __init__(self):
        """Initialize Layer 3 balance resolution engine."""
        pass

    def check_balance(
        self,
        db: Session,
        invoice: Optional[Invoice],
        po: PurchaseOrder,
        match_type: str,
        delivery_note: Optional[DeliveryNote] = None
    ) -> Dict:
        """
        Check balance status for a potential match.
        
        Args:
            db: Database session
            invoice: Invoice object (for INVOICE_PO or THREE_WAY)
            po: Purchase order object
            match_type: Type of matching being performed
            delivery_note: Delivery note object (for DELIVERY_NOTE_PO or THREE_WAY)
            
        Returns:
            Dictionary with balance information
        """
        result = {
            "has_remaining_balance": False,
            "po_remaining": Decimal("0"),
            "invoice_remaining": Decimal("0"),
            "dn_remaining": Decimal("0"),
            "can_full_match": True,
            "partial_match_amount": None
        }

        # Get existing balance entries for this PO
        po_balance = self._get_remaining_balance(db, po.id, BalanceType.PURCHASE_ORDER.value)
        po_remaining = po_balance.remaining_amount if po_balance else po.total_amount

        if po_remaining <= 0:
            result["has_remaining_balance"] = True
            result["can_full_match"] = False
            return result

        result["po_remaining"] = po_remaining

        # Check invoice balance if applicable
        if invoice and match_type in ("INVOICE_PO", "THREE_WAY"):
            inv_balance = self._get_remaining_balance(
                db, invoice.id, BalanceType.INVOICE.value
            )
            inv_remaining = inv_balance.remaining_amount if inv_balance else invoice.total_amount
            result["invoice_remaining"] = inv_remaining

            # Calculate if full match is possible
            if inv_remaining > po_remaining:
                result["can_full_match"] = False
                result["partial_match_amount"] = po_remaining
            else:
                result["partial_match_amount"] = inv_remaining

        # Check delivery note balance if applicable
        if delivery_note and match_type in ("DELIVERY_NOTE_PO", "THREE_WAY"):
            dn_balance = self._get_remaining_balance(
                db, delivery_note.id, BalanceType.DELIVERY_NOTE.value
            )
            dn_remaining = dn_balance.remaining_amount if dn_balance else delivery_note.total_amount
            result["dn_remaining"] = dn_remaining

            if dn_remaining > po_remaining:
                result["can_full_match"] = False

        return result

    def update_balance_ledger(
        self,
        db: Session,
        match_result: MatchResult,
        invoice: Optional[Invoice],
        po: PurchaseOrder,
        delivery_note: Optional[DeliveryNote],
        balance_info: Dict
    ) -> None:
        """
        Update balance ledger after a confirmed match.
        
        Args:
            db: Database session
            match_result: The match result record
            invoice: Invoice object (if applicable)
            po: Purchase order object
            delivery_note: Delivery note object (if applicable)
            balance_info: Balance information from check_balance
        """
        match_amount = balance_info.get("partial_match_amount", Decimal("0"))

        # Update PO balance
        self._update_or_create_balance(
            db,
            BalanceType.PURCHASE_ORDER.value,
            po.id,
            po.po_number,
            po.total_amount,
            match_amount,
            match_result.id
        )

        # Update invoice balance
        if invoice:
            self._update_or_create_balance(
                db,
                BalanceType.INVOICE.value,
                invoice.id,
                invoice.invoice_number,
                invoice.total_amount,
                match_amount,
                match_result.id
            )

        # Update delivery note balance
        if delivery_note:
            self._update_or_create_balance(
                db,
                BalanceType.DELIVERY_NOTE.value,
                delivery_note.id,
                delivery_note.dn_number,
                delivery_note.total_amount,
                match_amount,
                match_result.id
            )

    def get_document_balance(
        self,
        db: Session,
        document_id: str,
        document_type: str
    ) -> Dict:
        """
        Get current balance for a document.
        
        Args:
            db: Database session
            document_id: Document UUID
            document_type: Type of document (INVOICE, DELIVERY_NOTE, PURCHASE_ORDER)
            
        Returns:
            Dictionary with balance details
        """
        balance = self._get_remaining_balance(db, document_id, document_type)

        if not balance:
            return {
                "has_balance_record": False,
                "remaining_amount": None,
                "is_settled": True
            }

        return {
            "has_balance_record": True,
            "document_id": document_id,
            "document_type": document_type,
            "original_amount": float(balance.original_amount),
            "matched_amount": float(balance.matched_amount),
            "remaining_amount": float(balance.remaining_amount),
            "is_settled": balance.is_settled == "TRUE"
        }

    def settle_balance(
        self,
        db: Session,
        document_id: str,
        document_type: str
    ) -> bool:
        """
        Mark a balance as settled.
        
        Args:
            db: Database session
            document_id: Document UUID
            document_type: Type of document
            
        Returns:
            True if settled, False if not found
        """
        balance = self._get_remaining_balance(db, document_id, document_type)

        if not balance:
            return False

        balance.is_settled = "TRUE"
        balance.remaining_amount = Decimal("0")
        db.commit()

        return True

    def _get_remaining_balance(
        self,
        db: Session,
        document_id: str,
        document_type: str
    ) -> Optional[BalanceLedger]:
        """Get the most recent balance record for a document."""
        return db.query(BalanceLedger).filter(
            BalanceLedger.document_id == document_id,
            BalanceLedger.document_type == document_type,
            BalanceLedger.is_deleted == False,  # noqa: E712
            BalanceLedger.is_settled == "FALSE"  # noqa: E712
        ).order_by(BalanceLedger.created_at.desc()).first()

    def _update_or_create_balance(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        document_number: str,
        original_amount: Decimal,
        matched_amount: Decimal,
        match_result_id: str
    ) -> BalanceLedger:
        """
        Update or create a balance ledger entry.
        
        If a balance record exists, update it.
        Otherwise, create a new record.
        """
        existing = self._get_remaining_balance(db, document_id, document_type)

        if existing:
            existing.matched_amount += matched_amount
            existing.remaining_amount = existing.original_amount - existing.matched_amount
            existing.match_result_id = match_result_id

            if existing.remaining_amount <= 0:
                existing.is_settled = "TRUE"

            db.commit()
            return existing
        else:
            remaining = original_amount - matched_amount
            new_balance = BalanceLedger(
                document_type=document_type,
                document_id=document_id,
                document_number=document_number,
                balance_type=document_type,
                original_amount=original_amount,
                matched_amount=matched_amount,
                remaining_amount=remaining,
                currency="USD",
                match_result_id=match_result_id,
                is_settled="TRUE" if remaining <= 0 else "FALSE"
            )
            db.add(new_balance)
            db.commit()
            return new_balance
