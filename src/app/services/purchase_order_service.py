// src/app/services/purchase_order_service.py
"""
Purchase Order service.
"""
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.models.supplier import Supplier
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate
from app.services.base_service import BaseService


class PurchaseOrderService(BaseService[PurchaseOrder]):
    """Service for Purchase Order operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PurchaseOrder, session)

    async def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get PO by PO number."""
        return await self.get_by("po_number", po_number, load_relations=["lines", "supplier"])

    async def get_with_relations(self, id: UUID) -> Optional[PurchaseOrder]:
        """Get PO with all relations loaded."""
        result = await self.session.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.lines),
                selectinload(PurchaseOrder.supplier),
            )
            .where(PurchaseOrder.id == id)
        )
        return result.scalar_one_or_none()

    async def get_open_pos(
        self,
        supplier_id: UUID = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PurchaseOrder]:
        """Get all open (unfulfilled) POs."""
        stmt = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.status == "open")
        )
        if supplier_id:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_pos(
        self,
        query: str = None,
        supplier_id: UUID = None,
        status: str = None,
        date_from: date = None,
        date_to: date = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PurchaseOrder]:
        """Search purchase orders."""
        stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
        
        if query:
            stmt = stmt.where(PurchaseOrder.po_number.ilike(f"%{query}%"))
        if supplier_id:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)
        if date_from:
            stmt = stmt.where(PurchaseOrder.order_date >= date_from)
        if date_to:
            stmt = stmt.where(PurchaseOrder.order_date <= date_to)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_po(self, po_in: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a new purchase order with lines."""
        po_data = po_in.model_dump(exclude={"lines"})
        
        # Calculate totals from lines
        lines_data = po_data.pop("lines")
        subtotal = sum(line["line_total"] for line in lines_data)
        po_data["subtotal"] = subtotal
        po_data["tax_amount"] = Decimal("0.00")  # Can be calculated if tax rates provided
        po_data["total_amount"] = subtotal + po_data["tax_amount"]
        
        # Create PO
        po = PurchaseOrder(**po_data)
        self.session.add(po)
        await self.session.flush()
        
        # Create lines
        for line_data in lines_data:
            line = PurchaseOrderLine(purchase_order_id=po.id, **line_data)
            self.session.add(line)
        
        await self.session.flush()
        await self.session.refresh(po)
        
        return await self.get_with_relations(po.id)

    async def update_po(
        self, id: UUID, po_in: PurchaseOrderUpdate
    ) -> Optional[PurchaseOrder]:
        """Update a purchase order."""
        update_data = po_in.model_dump(exclude_unset=True)
        return await self.update(id, update_data)

    async def update_po_status(self, id: UUID, status: str) -> Optional[PurchaseOrder]:
        """Update PO status."""
        return await self.update(id, {"status": status})

    async def close_po(self, id: UUID) -> Optional[PurchaseOrder]:
        """Close a purchase order."""
        return await self.update_po_status(id, "closed")

    async def cancel_po(self, id: UUID) -> Optional[PurchaseOrder]:
        """Cancel a purchase order."""
        return await self.update_po_status(id, "cancelled")

    async def get_unmatched_pos(
        self,
        supplier_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PurchaseOrder]:
        """Get POs that haven't been fully matched."""
        stmt = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .outerjoin(PurchaseOrder.matched_invoices)
            .where(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_(["open", "partial"]),
            )
            .group_by(PurchaseOrder.id)
            .having(func.count(PurchaseOrder.matched_invoices) == 0)
        )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def calculate_open_amount(self, id: UUID) -> Decimal:
        """Calculate the remaining open amount for a PO."""
        po = await self.get_with_relations(id)
        if not po:
            return Decimal("0.00")
        
        # Get matched amount from balance ledger
        from sqlalchemy import text
        result = await self.session.execute(
            text("""
                SELECT COALESCE(SUM(matched_amount), 0) as matched
                FROM balance_ledger
                WHERE po_id = :po_id AND is_settled != 'settled'
            """),
            {"po_id": str(id)}
        )
        matched_amount = result.scalar() or Decimal("0.00")
        
        return po.total_amount - matched_amount
