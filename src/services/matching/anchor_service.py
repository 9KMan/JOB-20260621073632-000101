// src/services/matching/anchor_service.py
"""Layer 1: PO Anchoring Service.

This service establishes the PO as the single source of truth when matching
invoices or delivery notes. It performs initial anchoring by matching documents
to open POs based on supplier and PO number.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.document import PurchaseOrder, Invoice, DeliveryNote, DocumentStatus
from app.config import get_settings

settings = get_settings()


class AnchorService:
    """Service for PO anchoring (Layer 1 of the matching engine)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def anchor_invoice_to_po(self, invoice_id: str) -> Optional[PurchaseOrder]:
        """Attempt to anchor an invoice to an open PO.

        Anchoring is based on:
        1. Same supplier ID
        2. Invoice linked to PO or PO number in invoice metadata
        """
        # Get invoice
        result = await self.db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            return None

        # If already has PO, verify it
        if invoice.po_id:
            result = await self.db.execute(
                select(PurchaseOrder)
                .options(selectinload(PurchaseOrder.lines))
                .where(
                    PurchaseOrder.id == invoice.po_id,
                    PurchaseOrder.supplier_id == invoice.supplier_id,
                    PurchaseOrder.status.in_([DocumentStatus.PENDING, DocumentStatus.PARTIALLY_MATCHED]),
                )
            )
            po = result.scalar_one_or_none()
            if po:
                return po

        # Try to find open PO by supplier
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                PurchaseOrder.supplier_id == invoice.supplier_id,
                PurchaseOrder.status.in_([DocumentStatus.PENDING, DocumentStatus.PARTIALLY_MATCHED]),
            )
            .order_by(PurchaseOrder.order_date.desc())
            .limit(1)
        )
        po = result.scalar_one_or_none()
        if po:
            # Update invoice with PO reference
            invoice.po_id = po.id
            await self.db.flush()
        return po

    async def anchor_delivery_note_to_po(self, delivery_note_id: str) -> Optional[PurchaseOrder]:
        """Attempt to anchor a delivery note to an open PO.

        Anchoring is based on:
        1. Same supplier ID
        2. DN linked to PO or PO number in DN metadata
        """
        # Get delivery note
        result = await self.db.execute(
            select(DeliveryNote).where(DeliveryNote.id == delivery_note_id)
        )
        dn = result.scalar_one_or_none()
        if not dn:
            return None

        # If already has PO, verify it
        if dn.po_id:
            result = await self.db.execute(
                select(PurchaseOrder)
                .options(selectinload(PurchaseOrder.lines))
                .where(
                    PurchaseOrder.id == dn.po_id,
                    PurchaseOrder.supplier_id == dn.supplier_id,
                    PurchaseOrder.status.in_([DocumentStatus.PENDING, DocumentStatus.PARTIALLY_MATCHED]),
                )
            )
            po = result.scalar_one_or_none()
            if po:
                return po

        # Try to find open PO by supplier
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                PurchaseOrder.supplier_id == dn.supplier_id,
                PurchaseOrder.status.in_([DocumentStatus.PENDING, DocumentStatus.PARTIALLY_MATCHED]),
            )
            .order_by(PurchaseOrder.order_date.desc())
            .limit(1)
        )
        po = result.scalar_one_or_none()
        if po:
            # Update DN with PO reference
            dn.po_id = po.id
            await self.db.flush()
        return po

    async def find_anchor_po(self, supplier_id: str, po_number: Optional[str] = None) -> Optional[PurchaseOrder]:
        """Find the anchor PO for a given supplier.

        If po_number is provided, find that specific PO.
        Otherwise, find the most recent open PO for the supplier.
        """
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines)).where(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status.in_([DocumentStatus.PENDING, DocumentStatus.PARTIALLY_MATCHED]),
        )

        if po_number:
            query = query.where(PurchaseOrder.po_number == po_number)

        query = query.order_by(PurchaseOrder.order_date.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_anchor_status(self, po_id: str) -> dict:
        """Get the anchoring status for a PO.

        Returns statistics about how much of the PO has been matched.
        """
        from app.models.balance import BalanceLedger, BalanceType
        from sqlalchemy import func
        from decimal import Decimal

        # Get all balances for this PO
        result = await self.db.execute(
            select(BalanceLedger).where(
                BalanceLedger.po_id == po_id,
                BalanceLedger.balance_type == BalanceType.PO_OPEN,
            )
        )
        open_balance = result.scalar_one_or_none()

        if not open_balance:
            # No balance record, PO is untouched
            po_result = await self.db.execute(
                select(PurchaseOrder)
                .options(selectinload(PurchaseOrder.lines))
                .where(PurchaseOrder.id == po_id)
            )
            po = po_result.scalar_one_or_none()
            if po:
                return {
                    "po_id": po_id,
                    "po_number": po.po_number,
                    "total_amount": po.total_amount,
                    "total_quantity": sum(line.quantity for line in po.lines),
                    "billed_amount": Decimal("0"),
                    "billed_quantity": Decimal("0"),
                    "remaining_amount": po.total_amount,
                    "remaining_quantity": sum(line.quantity for line in po.lines),
                    "matched_percentage": Decimal("0"),
                }

        return {
            "po_id": po_id,
            "remaining_amount": open_balance.remaining_amount,
            "remaining_quantity": open_balance.remaining_quantity,
            "billed_amount": open_balance.billed_amount,
            "billed_quantity": open_balance.billed_quantity,
            "original_amount": open_balance.original_amount,
            "original_quantity": open_balance.original_quantity,
            "matched_percentage": (
                (open_balance.original_amount - open_balance.remaining_amount) / open_balance.original_amount * 100
                if open_balance.original_amount > 0
                else Decimal("0")
            ),
        }
