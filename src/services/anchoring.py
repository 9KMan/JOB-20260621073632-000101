// src/services/anchoring.py
"""Layer 1: Anchoring service using PO as single source of truth."""

from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.models.invoice import Invoice, InvoiceLine
from app.models.delivery_note import DeliveryNote, DeliveryNoteLine


class AnchoringService:
    """
    Layer 1 of the 3-way matching engine.
    
    Uses the Purchase Order as the single source of truth for anchoring.
    When an invoice or delivery note arrives, the system first tries to 
    match it against open POs by supplier and PO number.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_anchoring_po(
        self,
        supplier_code: str,
        po_number: Optional[str] = None,
        invoice_number: Optional[str] = None,
        dn_number: Optional[str] = None,
    ) -> Optional[PurchaseOrder]:
        """
        Find the anchoring Purchase Order based on supplier and document references.
        
        Search priority:
        1. Exact PO number match
        2. Match via invoice reference
        3. Match via delivery note reference
        """
        # Build base query for open POs
        base_query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.supplier_code == supplier_code,
                PurchaseOrder.status.in_(["OPEN", "PARTIAL"]),
                PurchaseOrder.is_deleted == False,
            )
        ).options(selectinload(PurchaseOrder.lines))

        # Priority 1: Direct PO number match
        if po_number:
            query = base_query.where(PurchaseOrder.po_number == po_number)
            result = await self.db.execute(query)
            po = result.scalar_one_or_none()
            if po:
                return po

        # Priority 2: Match via invoice reference (stored in PO notes or separate field)
        if invoice_number:
            query = base_query.where(PurchaseOrder.notes.contains(invoice_number))
            result = await self.db.execute(query)
            po = result.scalar_one_or_none()
            if po:
                return po

        # Priority 3: Match via delivery note reference
        if dn_number:
            query = base_query.where(PurchaseOrder.notes.contains(dn_number))
            result = await self.db.execute(query)
            po = result.scalar_one_or_none()
            if po:
                return po

        # Fallback: Return any open PO for this supplier
        query = base_query.order_by(PurchaseOrder.po_date.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_open_pos_for_supplier(
        self,
        supplier_code: str,
        limit: int = 10,
    ) -> List[PurchaseOrder]:
        """Get all open POs for a supplier."""
        query = (
            select(PurchaseOrder)
            .where(
                and_(
                    PurchaseOrder.supplier_code == supplier_code,
                    PurchaseOrder.status.in_(["OPEN", "PARTIAL"]),
                    PurchaseOrder.is_deleted == False,
                )
            )
            .options(selectinload(PurchaseOrder.lines))
            .order_by(PurchaseOrder.po_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def validate_po_anchor(
        self,
        po: PurchaseOrder,
        document_type: str,
        document_lines: List[Any],
    ) -> Dict[str, Any]:
        """
        Validate that a document can be anchored to the given PO.
        
        Returns validation result with details.
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "line_matches": [],
        }

        # Check PO status
        if po.status == "CLOSED":
            validation["is_valid"] = False
            validation["errors"].append("PO is closed and cannot accept new matches")
            return validation

        if po.status == "CANCELLED":
            validation["is_valid"] = False
            validation["errors"].append("PO is cancelled")
            return validation

        # Check currency match
        if document_type in ["INVOICE", "DELIVERY_NOTE"]:
            doc_currency = getattr(document_lines[0] if document_lines else None, "currency", None)
            if doc_currency and doc_currency != po.currency:
                validation["warnings"].append(
                    f"Currency mismatch: PO is {po.currency}, document is {doc_currency}"
                )

        return validation

    async def get_po_line_availability(self, po: PurchaseOrder) -> Dict[str, Dict[str, Any]]:
        """
        Get availability for each line in the PO.
        
        Returns dict mapping line_id to availability info.
        """
        availability = {}

        for line in po.lines:
            remaining_qty = line.quantity_ordered - line.quantity_received
            availability[str(line.id)] = {
                "line_id": str(line.id),
                "item_code": line.item_code,
                "quantity_ordered": line.quantity_ordered,
                "quantity_received": line.quantity_received,
                "remaining_quantity": remaining_qty,
                "is_available": remaining_qty > 0,
                "fill_percentage": (
                    (line.quantity_received / line.quantity_ordered * 100)
                    if line.quantity_ordered > 0
                    else Decimal("100.00")
                ),
            }

        return availability
