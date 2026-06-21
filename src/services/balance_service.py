// src/services/balance_service.py
"""Balance service for tracking and resolving partial matches."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import get_settings
from src.models.document import Document, DocumentType
from src.models.matching import BalanceLedger, BalanceType, BalanceStatus


class BalanceService:
    """Service for managing balance ledger and resolution."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def get_document_balance(self, document_id: UUID) -> list[BalanceLedger]:
        """Get all balance ledger entries for a document."""
        result = await self.db.execute(
            select(BalanceLedger)
            .where(BalanceLedger.document_id == str(document_id))
            .order_by(BalanceLedger.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_balance_entry(
        self,
        document: Document,
        reference_document: Optional[Document] = None,
        matched_amount: Decimal = Decimal("0")
    ) -> BalanceLedger:
        """Create a new balance ledger entry."""
        balance_amount = document.total_amount - matched_amount
        balance_type = (
            BalanceType.OVER if balance_amount > 0 else
            BalanceType.UNDER if balance_amount < 0 else
            BalanceType.MATCHED
        )

        entry = BalanceLedger(
            document_id=str(document.id),
            document_type=document.document_type.value,
            reference_document_id=str(reference_document.id) if reference_document else None,
            reference_document_type=reference_document.document_type.value if reference_document else None,
            original_amount=document.total_amount,
            matched_amount=matched_amount,
            balance_amount=balance_amount,
            balance_type=balance_type,
            currency=document.currency,
            status="OPEN"
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def update_balance_entry(
        self,
        balance_id: UUID,
        additional_matched: Decimal
    ) -> Optional[BalanceLedger]:
        """Update a balance entry with additional matched amount."""
        result = await self.db.execute(
            select(BalanceLedger).where(BalanceLedger.id == balance_id)
        )
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        entry.matched_amount += additional_matched
        entry.balance_amount = entry.original_amount - entry.matched_amount

        if entry.balance_amount == Decimal("0"):
            entry.balance_type = BalanceType.MATCHED
            entry.status = "RESOLVED"
        elif entry.balance_amount > 0:
            entry.balance_type = BalanceType.OVER
        else:
            entry.balance_type = BalanceType.UNDER

        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def resolve_balance(
        self,
        document_id: UUID,
        resolution_type: str,
        resolution_amount: Decimal,
        notes: Optional[str] = None
    ) -> bool:
        """
        Resolve a balance discrepancy.
        
        Resolution types:
        - WRITE_OFF: Write off the balance
        - ADJUST: Adjust the document to match
        - SPLIT: Split into multiple entries
        - DISPUTE: Mark as disputed
        """
        result = await self.db.execute(
            select(BalanceLedger)
            .where(BalanceLedger.document_id == str(document_id))
            .where(BalanceLedger.status == "OPEN")
        )
        entries = list(result.scalars().all())

        if not entries:
            return False

        resolved_at = datetime.utcnow()

        for entry in entries:
            if resolution_type == "WRITE_OFF":
                entry.matched_amount = entry.original_amount
                entry.balance_amount = Decimal("0")
                entry.balance_type = BalanceType.MATCHED
                entry.status = "RESOLVED"
            elif resolution_type == "ADJUST":
                entry.matched_amount = entry.original_amount
                entry.balance_amount = Decimal("0")
                entry.balance_type = BalanceType.MATCHED
                entry.status = "RESOLVED"
            elif resolution_type == "DISPUTE":
                entry.status = "DISPUTED"
            elif resolution_type == "SPLIT":
                # Create additional entries for split
                remaining = entry.balance_amount
                entry.balance_amount = Decimal("0")
                entry.matched_amount = entry.original_amount
                entry.status = "RESOLVED"
                entry.balance_type = BalanceType.MATCHED

                new_entry = BalanceLedger(
                    document_id=entry.document_id,
                    document_type=entry.document_type,
                    original_amount=remaining,
                    matched_amount=Decimal("0"),
                    balance_amount=remaining,
                    balance_type=entry.balance_type,
                    currency=entry.currency,
                    status="OPEN"
                )
                self.db.add(new_entry)

            entry.resolved_at = resolved_at
            entry.resolution_notes = notes

        await self.db.commit()
        return True

    async def get_outstanding_balances(
        self,
        document_type: Optional[str] = None,
        supplier_id: Optional[str] = None
    ) -> list[BalanceLedger]:
        """Get all outstanding (unresolved) balance entries."""
        query = select(BalanceLedger).where(BalanceLedger.status == "OPEN")

        if document_type:
            query = query.where(BalanceLedger.document_type == document_type)

        result = await self.db.execute(query.order_by(BalanceLedger.created_at.desc()))
        return list(result.scalars().all())

    async def reconcile_balances(
        self,
        invoice_id: UUID,
        po_id: UUID
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Reconcile balances between invoice and PO.
        
        Returns:
            Tuple of (invoice_balance, po_balance, net_variance)
        """
        # Get or create balance entries
        invoice_balance = await self._get_or_create_balance(invoice_id)
        po_balance = await self._get_or_create_balance(po_id)

        # Calculate matched amounts based on line-level matching
        matched = await self._calculate_matched_amounts(invoice_id, po_id)

        invoice_balance.matched_amount = matched
        invoice_balance.balance_amount = invoice_balance.original_amount - matched

        if invoice_balance.balance_amount > Decimal("0"):
            invoice_balance.balance_type = BalanceType.OVER
        elif invoice_balance.balance_amount < Decimal("0"):
            invoice_balance.balance_type = BalanceType.UNDER
        else:
            invoice_balance.balance_type = BalanceType.MATCHED
            invoice_balance.status = "RESOLVED"

        await self.db.commit()

        net_variance = abs(invoice_balance.balance_amount)

        return invoice_balance.balance_amount, po_balance.balance_amount, net_variance

    async def _get_or_create_balance(self, document_id: UUID) -> BalanceLedger:
        """Get existing or create new balance entry for a document."""
        result = await self.db.execute(
            select(BalanceLedger).where(BalanceLedger.document_id == str(document_id))
        )
        entry = result.scalar_one_or_none()

        if not entry:
            doc_result = await self.db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = doc_result.scalar_one_or_none()

            if document:
                entry = await self.create_balance_entry(document)
            else:
                raise ValueError(f"Document {document_id} not found")

        return entry

    async def _calculate_matched_amounts(self, invoice_id: UUID, po_id: UUID) -> Decimal:
        """Calculate matched amounts between invoice and PO lines."""
        from src.models.document import DocumentLine
        from sqlalchemy.orm import selectinload

        # This is a simplified version - full implementation would use line matching
        invoice_result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.lines))
            .where(Document.id == invoice_id)
        )
        invoice = invoice_result.scalar_one_or_none()

        po_result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.lines))
            .where(Document.id == po_id)
        )
        po = po_result.scalar_one_or_none()

        if not invoice or not po:
            return Decimal("0")

        # Simple amount-based matching
        invoice_total = invoice.total_amount
        po_total = po.total_amount

        if po_total > 0:
            ratio = min(invoice_total / po_total, Decimal("1"))
            return po_total * ratio

        return Decimal("0")
