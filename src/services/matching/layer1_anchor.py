// src/services/matching/layer1_anchor.py
"""Layer 1: Anchoring Service - Match documents against POs."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.purchase_order import PurchaseOrder, PurchaseOrderLine
from models.invoice import Invoice, InvoiceLine
from models.delivery_note import DeliveryNote, DeliveryNoteLine
from models.match import Match, MatchType


class Layer1AnchorService:
    """
    Layer 1 - Anchoring Service
    
    Uses the Purchase Order as the single source of truth for anchoring.
    When an invoice or delivery note arrives, the system first tries to match
    it against open POs by supplier and PO number.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def anchor_document(
        self,
        document_type: str,
        document_id: uuid.UUID,
    ) -> Optional[PurchaseOrder]:
        """
        Anchor a document to its corresponding Purchase Order.
        
        Args:
            document_type: Type of document (PO, Invoice, DN)
            document_id: UUID of the document
            
        Returns:
            The anchored PurchaseOrder if found, None otherwise
        """
        if document_type == "PO":
            return await self._anchor_po(document_id)
        elif document_type == "Invoice":
            return await self._anchor_invoice(document_id)
        elif document_type == "DN":
            return await self._anchor_delivery_note(document_id)
        return None

    async def _anchor_po(self, po_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """Get PO - it's already the anchor."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()

    async def _anchor_invoice(self, invoice_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """
        Anchor an invoice to a PO by matching supplier and PO number.
        
        Returns the PO that this invoice should be anchored to.
        """
        # Get the invoice
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines))
            .where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return None
        
        # Try to find matching PO by supplier and PO number
        query = select(PurchaseOrder).where(
            PurchaseOrder.supplier_code == invoice.supplier_code,
            PurchaseOrder.po_number == invoice.po_number,
            PurchaseOrder.status == "OPEN",
            PurchaseOrder.is_deleted == False,
        )
        
        result = await self.db.execute(query)
        po = result.scalar_one_or_none()
        
        if po:
            # Update invoice with PO reference
            invoice.purchase_order_id = po.id
            await self.db.flush()
        
        return po

    async def _anchor_delivery_note(self, dn_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """
        Anchor a delivery note to a PO by matching supplier and PO number.
        
        Returns the PO that this delivery note should be anchored to.
        """
        # Get the delivery note
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.id == dn_id)
        )
        dn = result.scalar_one_or_none()
        
        if not dn:
            return None
        
        # Try to find matching PO by supplier and PO number
        query = select(PurchaseOrder).where(
            PurchaseOrder.supplier_code == dn.supplier_code,
            PurchaseOrder.po_number == dn.po_number,
            PurchaseOrder.status == "OPEN",
            PurchaseOrder.is_deleted == False,
        )
        
        result = await self.db.execute(query)
        po = result.scalar_one_or_none()
        
        if po:
            # Update DN with PO reference
            dn.purchase_order_id = po.id
            await self.db.flush()
        
        return po

    async def find_anchor_po(
        self,
        supplier_code: str,
        po_number: str,
    ) -> Optional[PurchaseOrder]:
        """
        Find an open PO by supplier code and PO number.
        
        This is the core anchoring logic used to establish the
        deterministic anchor for all downstream matching.
        """
        query = select(PurchaseOrder).where(
            PurchaseOrder.supplier_code == supplier_code,
            PurchaseOrder.po_number == po_number,
            PurchaseOrder.status == "OPEN",
            PurchaseOrder.is_deleted == False,
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_anchor_chain(
        self,
        document_type: str,
        document_id: uuid.UUID,
    ) -> Tuple[Optional[PurchaseOrder], list]:
        """
        Get the complete anchor chain for a document.
        
        Returns:
            Tuple of (anchor PO, list of intermediate matches)
        """
        anchor_po = await self.anchor_document(document_type, document_id)
        
        if not anchor_po:
            return None, []
        
        # Get any existing matches for this PO
        match_query = select(Match).where(
            Match.purchase_order_id == anchor_po.id,
        )
        result = await self.db.execute(match_query)
        existing_matches = result.scalars().all()
        
        return anchor_po, list(existing_matches)
