// src/services/balance_resolution.py
"""Layer 3: Balance Resolution service for tracking partial matches."""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.balance import BalanceLedger, BalanceEntry
from app.models.purchase_order import PurchaseOrderLine


class BalanceResolutionService:
    """
    Layer 3 of the 3-way matching engine.
    
    Tracks partial matches and balances across all three document types:
    - Partial shipments
    - Split invoices
    - Multi-delivery scenarios
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_ledger(
        self,
        document_type: str,
        document_id: str,
        po_line_id: Optional[str] = None,
        original_amount: Optional[Decimal] = None,
        original_quantity: Optional[Decimal] = None,
    ) -> BalanceLedger:
        """
        Get existing or create new balance ledger for a document.
        """
        # Try to find existing ledger
        query = select(BalanceLedger).where(
            and_(
                BalanceLedger.document_type == document_type,
                BalanceLedger.document_id == document_id,
                BalanceLedger.is_active == True,
            )
        )
        result = await self.db.execute(query)
        ledger = result.scalar_one_or_none()

        if ledger is None:
            # Create new ledger
            ledger = BalanceLedger(
                document_type=document_type,
                document_id=document_id,
                po_line_id=po_line_id,
                original_amount=original_amount or Decimal("0.00"),
                matched_amount=Decimal("0.00"),
                remaining_amount=original_amount or Decimal("0.00"),
                original_quantity=original_quantity or Decimal("0.00"),
                matched_quantity=Decimal("0.00"),
                remaining_quantity=original_quantity or Decimal("0.00"),
                status="OPEN",
            )
            self.db.add(ledger)
            await self.db.commit()
            await self.db.refresh(ledger)

        return ledger

    async def record_match(
        self,
        ledger: BalanceLedger,
        match_id: str,
        amount: Decimal,
        quantity: Decimal,
        notes: Optional[str] = None,
    ) -> BalanceEntry:
        """
        Record a match against a ledger, updating the balance.
        """
        balance_before = ledger.remaining_amount
        quantity_before = ledger.remaining_quantity

        # Update ledger
        ledger.matched_amount += amount
        ledger.matched_quantity += quantity
        ledger.remaining_amount -= amount
        ledger.remaining_quantity -= quantity

        # Check if fully matched
        if ledger.remaining_amount <= Decimal("0.01") and ledger.remaining_quantity <= Decimal("0.001"):
            ledger.status = "CLOSED"
        elif ledger.matched_amount > 0:
            ledger.status = "PARTIAL"

        # Create balance entry
        entry = BalanceEntry(
            ledger_id=str(ledger.id),
            match_id=match_id,
            entry_type="MATCH",
            amount=amount,
            quantity=quantity,
            balance_before=balance_before,
            balance_after=ledger.remaining_amount,
            notes=notes,
        )
        self.db.add(entry)
        await self.db.commit()

        return entry

    async def reverse_match(
        self,
        ledger: BalanceLedger,
        match_id: str,
        notes: Optional[str] = None,
    ) -> Optional[BalanceEntry]:
        """
        Reverse a match and restore the balance.
        """
        # Find the original match entry
        query = select(BalanceEntry).where(
            and_(
                BalanceEntry.ledger_id == str(ledger.id),
                BalanceEntry.match_id == match_id,
                BalanceEntry.entry_type == "MATCH",
            )
        )
        result = await self.db.execute(query)
        original_entry = result.scalar_one_or_none()

        if original_entry is None:
            return None

        balance_before = ledger.remaining_amount

        # Restore balance
        ledger.matched_amount -= original_entry.amount
        ledger.matched_quantity -= original_entry.quantity
        ledger.remaining_amount += original_entry.amount
        ledger.remaining_quantity += original_entry.quantity

        # Update status
        if ledger.remaining_amount > Decimal("0.01"):
            ledger.status = "PARTIAL"
        else:
            ledger.status = "OPEN"

        # Create reversal entry
        reversal = BalanceEntry(
            ledger_id=str(ledger.id),
            match_id=match_id,
            entry_type="REVERSAL",
            amount=-original_entry.amount,
            quantity=-original_entry.quantity,
            balance_before=balance_before,
            balance_after=ledger.remaining_amount,
            notes=notes or f"Reversal of match {match_id}",
        )
        self.db.add(reversal)
        await self.db.commit()

        return reversal

    async def adjust_balance(
        self,
        ledger: BalanceLedger,
        amount_adjustment: Decimal,
        quantity_adjustment: Decimal,
        notes: str,
    ) -> BalanceEntry:
        """
        Make a manual balance adjustment (e.g., for write-offs or corrections).
        """
        balance_before = ledger.remaining_amount

        ledger.original_amount += amount_adjustment
        ledger.remaining_amount += amount_adjustment
        ledger.original_quantity += quantity_adjustment
        ledger.remaining_quantity += quantity_adjustment

        entry = BalanceEntry(
            ledger_id=str(ledger.id),
            entry_type="ADJUSTMENT",
            amount=amount_adjustment,
            quantity=quantity_adjustment,
            balance_before=balance_before,
            balance_after=ledger.remaining_amount,
            notes=notes,
        )
        self.db.add(entry)
        await self.db.commit()

        return entry

    async def get_ledger_balance(
        self,
        document_type: str,
        document_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current balance for a document.
        """
        query = select(BalanceLedger).where(
            and_(
                BalanceLedger.document_type == document_type,
                BalanceLedger.document_id == document_id,
                BalanceLedger.is_active == True,
            )
        )
        result = await self.db.execute(query)
        ledger = result.scalar_one_or_none()

        if ledger is None:
            return None

        return {
            "ledger_id": str(ledger.id),
            "document_type": ledger.document_type,
            "document_id": ledger.document_id,
            "original_amount": ledger.original_amount,
            "matched_amount": ledger.matched_amount,
            "remaining_amount": ledger.remaining_amount,
            "original_quantity": ledger.original_quantity,
            "matched_quantity": ledger.matched_quantity,
            "remaining_quantity": ledger.remaining_quantity,
            "status": ledger.status,
            "is_balanced": ledger.is_balanced,
        }

    async def get_open_balances_for_po_line(
        self,
        po_line_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all open balances for a specific PO line.
        """
        query = select(BalanceLedger).where(
            and_(
                BalanceLedger.po_line_id == po_line_id,
                BalanceLedger.status.in_(["OPEN", "PARTIAL"]),
                BalanceLedger.is_active == True,
            )
        )
        result = await self.db.execute(query)
        ledgers = result.scalars().all()

        return [
            {
                "ledger_id": str(ledger.id),
                "document_type": ledger.document_type,
                "document_id": ledger.document_id,
                "remaining_amount": ledger.remaining_amount,
                "remaining_quantity": ledger.remaining_quantity,
                "status": ledger.status,
            }
            for ledger in ledgers
        ]

    async def consolidate_partial_matches(
        self,
        document_type: str,
        document_id: str,
        match_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Consolidate multiple partial matches into a single balance view.
        """
        # Get the main ledger
        main_balance = await self.get_ledger_balance(document_type, document_id)

        if main_balance is None:
            return {
                "consolidated": False,
                "error": "No ledger found for document",
            }

        # Calculate total matched across all match IDs
        total_matched = Decimal("0.00")
        total_matched_qty = Decimal("0.00")

        for match_id in match_ids:
            # Sum up entries for each match
            query = select(BalanceEntry).where(
                and_(
                    BalanceEntry.ledger_id == main_balance["ledger_id"],
                    BalanceEntry.match_id == match_id,
                    BalanceEntry.entry_type == "MATCH",
                )
            )
            result = await self.db.execute(query)
            entries = result.scalars().all()

            for entry in entries:
                total_matched += entry.amount
                total_matched_qty += entry.quantity

        return {
            "consolidated": True,
            "document_type": document_type,
            "document_id": document_id,
            "original_amount": main_balance["original_amount"],
            "total_consolidated_match": total_matched,
            "total_consolidated_quantity": total_matched_qty,
            "remaining_after_consolidation": main_balance["original_amount"] - total_matched,
            "match_count": len(match_ids),
        }
