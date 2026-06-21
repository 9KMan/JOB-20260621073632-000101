// src/app/services/anchoring_service.py
"""
Layer 1 — Anchoring Service

Uses the Purchase Order as the single source of truth for anchoring.
When an invoice or delivery note arrives, the system first tries to match
it against open POs by supplier and PO number.
"""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.app.models.invoice import Invoice, InvoiceLine
from src.app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.app.schemas.match import MatchScore, MatchVariance


class AnchoringResult:
    """Result of anchoring operation."""

    def __init__(
        self,
        success: bool,
        po_id: UUID | None = None,
        po_number: str | None = None,
        supplier_match: bool = False,
        po_match: bool = False,
        confidence: Decimal = Decimal("0.0"),
        message: str = "",
    ):
        self.success = success
        self.po_id = po_id
        self.po_number = po_number
        self.supplier_match = supplier_match
        self.po_match = po_match
        self.confidence = confidence
        self.message = message


class AnchoringService:
    """
    Layer 1 of the 3-Way Matching Engine.
    
    Anchoring establishes a deterministic relationship between incoming
    documents (Invoice, Delivery Note) and a Purchase Order.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def anchor_invoice_to_po(
        self,
        invoice_id: UUID,
        supplier_id: str | None = None,
        po_number: str | None = None,
    ) -> AnchoringResult:
        """
        Attempt to anchor an invoice to a Purchase Order.
        
        The anchor is established by:
        1. Matching supplier_id between invoice and PO
        2. Optionally matching PO number if provided
        """
        # Build query conditions
        conditions = [
            PurchaseOrder.status == "OPEN",
            PurchaseOrder.is_deleted == False,
        ]
        
        if supplier_id:
            conditions.append(PurchaseOrder.supplier_id == supplier_id)
        
        if po_number:
            conditions.append(PurchaseOrder.po_number == po_number)
        
        result = await self.db.execute(
            select(PurchaseOrder)
            .where(and_(*conditions))
            .options(selectinload(PurchaseOrder.lines))
            .order_by(PurchaseOrder.created_at.desc())
            .limit(1)
        )
        
        po = result.scalar_one_or_none()
        
        if not po:
            return AnchoringResult(
                success=False,
                message=f"No matching open Purchase Order found for supplier {supplier_id}",
            )
        
        # Calculate confidence based on matching criteria
        confidence = Decimal("0.0")
        supplier_match = supplier_id == po.supplier_id if supplier_id else False
        po_match = po_number == po.po_number if po_number else False
        
        if supplier_match and po_match:
            confidence = Decimal("1.0")
        elif supplier_match:
            confidence = Decimal("0.8")
        else:
            confidence = Decimal("0.5")
        
        return AnchoringResult(
            success=True,
            po_id=po.id,
            po_number=po.po_number,
            supplier_match=supplier_match,
            po_match=po_match,
            confidence=confidence,
            message=f"Invoice anchored to PO {po.po_number}",
        )

    async def anchor_delivery_note_to_po(
        self,
        dn_id: UUID,
        supplier_id: str | None = None,
        po_number: str | None = None,
    ) -> AnchoringResult:
        """
        Attempt to anchor a delivery note to a Purchase Order.
        """
        conditions = [
            PurchaseOrder.status == "OPEN",
            PurchaseOrder.is_deleted == False,
        ]
        
        if supplier_id:
            conditions.append(PurchaseOrder.supplier_id == supplier_id)
        
        if po_number:
            conditions.append(PurchaseOrder.po_number == po_number)
        
        result = await self.db.execute(
            select(PurchaseOrder)
            .where(and_(*conditions))
            .options(selectinload(PurchaseOrder.lines))
            .order_by(PurchaseOrder.created_at.desc())
            .limit(1)
        )
        
        po = result.scalar_one_or_none()
        
        if not po:
            return AnchoringResult(
                success=False,
                message=f"No matching open Purchase Order found for supplier {supplier_id}",
            )
        
        confidence = Decimal("0.0")
        supplier_match = supplier_id == po.supplier_id if supplier_id else False
        po_match = po_number == po.po_number if po_number else False
        
        if supplier_match and po_match:
            confidence = Decimal("1.0")
        elif supplier_match:
            confidence = Decimal("0.8")
        
        return AnchoringResult(
            success=True,
            po_id=po.id,
            po_number=po.po_number,
            supplier_match=supplier_match,
            po_match=po_match,
            confidence=confidence,
            message=f"Delivery Note anchored to PO {po.po_number}",
        )

    async def find_potential_anchor_pos(
        self,
        supplier_id: str,
        limit: int = 10,
    ) -> list[PurchaseOrder]:
        """
        Find potential POs that could serve as anchors for new documents.
        """
        result = await self.db.execute(
            select(PurchaseOrder)
            .where(
                and_(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.status == "OPEN",
                    PurchaseOrder.is_deleted == False,
                )
            )
            .options(selectinload(PurchaseOrder.lines))
            .order_by(PurchaseOrder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_po_for_anchoring(self, po_id: UUID) -> PurchaseOrder | None:
        """Get a PO with its lines for anchoring purposes."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .where(
                and_(
                    PurchaseOrder.id == po_id,
                    PurchaseOrder.is_deleted == False,
                )
            )
            .options(selectinload(PurchaseOrder.lines))
        )
        return result.scalar_one_or_none()
