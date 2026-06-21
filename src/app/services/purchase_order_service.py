// src/app/services/purchase_order_service.py
"""
Purchase Order Service
Handles PO-related business logic.
"""
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.models.invoice import Invoice
from app.models.delivery_note import DeliveryNote
from app.services.base import BaseService


class PurchaseOrderService(BaseService[PurchaseOrder]):
    """Service for Purchase Order operations."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(PurchaseOrder, session)
    
    async def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get PO by PO number."""
        session = await self._get_session()
        result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        )
        return result.scalar_one_or_none()
    
    async def get_with_lines(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get PO with all lines."""
        session = await self._get_session()
        result = await session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()
    
    async def get_open_pos_by_supplier(self, supplier_id: UUID) -> List[PurchaseOrder]:
        """Get all open POs for a supplier."""
        session = await self._get_session()
        result = await session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_(["approved", "partial"])
            )
        )
        return list(result.scalars().all())
    
    async def create_po(self, data: dict) -> PurchaseOrder:
        """Create new PO with lines."""
        session = await self._get_session()
        
        # Extract lines data
        lines_data = data.pop("lines", [])
        
        # Calculate totals
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")
        
        for line in lines_data:
            line_amount = line["quantity"] * line["unit_price"]
            line_tax = line_amount * line.get("tax_rate", Decimal("0"))
            line["line_amount"] = line_amount
            line["tax_amount"] = line_tax
            line["total_amount"] = line_amount + line_tax
            line["quantity_received"] = Decimal("0")
            
            subtotal += line_amount
            total_tax += line_tax
        
        data["subtotal"] = subtotal
        data["tax_amount"] = total_tax
        data["total_amount"] = subtotal + total_tax
        
        # Create PO
        po = PurchaseOrder(**data)
        session.add(po)
        await session.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data["po_id"] = po.id
            line = PurchaseOrderLine(**line_data)
            session.add(line)
        
        await session.flush()
        await session.refresh(po)
        
        return await self.get_with_lines(po.id)
    
    async def update_po(self, po_id: UUID, data: dict) -> Optional[PurchaseOrder]:
        """Update PO and recalculate totals if needed."""
        session = await self._get_session()
        
        if "lines" in data:
            # Handle line updates separately
            lines_data = data.pop("lines")
            # Update lines logic would go here
            pass
        
        # Recalculate totals if quantities/prices changed
        if any(k in data for k in ["subtotal", "tax_amount", "total_amount"]):
            po = await self.get_with_lines(po_id)
            if po:
                subtotal = sum(line.line_amount for line in po.lines)
                tax_amount = sum(line.tax_amount for line in po.lines)
                total_amount = subtotal + tax_amount
                
                data["subtotal"] = subtotal
                data["tax_amount"] = tax_amount
                data["total_amount"] = total_amount
        
        return await self.update(po_id, data)
    
    async def update_status(self, po_id: UUID, status: str) -> Optional[PurchaseOrder]:
        """Update PO status."""
        return await self.update(po_id, {"status": status})
    
    async def approve(self, po_id: UUID, approved_by: UUID) -> Optional[PurchaseOrder]:
        """Approve a PO."""
        from datetime import datetime
        return await self.update(po_id, {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow()
        })
    
    async def get_statistics(self) -> dict:
        """Get PO statistics."""
        session = await self._get_session()
        
        total = await session.execute(select(func.count(PurchaseOrder.id)))
        draft = await session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.status == "draft")
        )
        approved = await session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.status == "approved")
        )
        closed = await session.execute(
            select(func.count(PurchaseOrder.id))
            .where(PurchaseOrder.status == "closed")
        )
        
        return {
            "total": total.scalar_one(),
            "draft": draft.scalar_one(),
            "approved": approved.scalar_one(),
            "closed": closed.scalar_one(),
        }
