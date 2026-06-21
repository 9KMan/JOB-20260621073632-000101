// app/services/purchase_order.py
"""Purchase Order service."""
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    """Service for purchase order operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_po_by_id(self, po_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """Get a purchase order by ID with lines."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                and_(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_po_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get a purchase order by PO number."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                and_(PurchaseOrder.po_number == po_number, PurchaseOrder.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_open_pos_by_vendor(
        self,
        vendor_id: uuid.UUID,
        po_number: Optional[str] = None,
    ) -> List[PurchaseOrder]:
        """Get open (non-closed, non-cancelled) POs for a vendor."""
        query = select(PurchaseOrder).options(
            selectinload(PurchaseOrder.lines)
        ).where(
            and_(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.is_deleted == False,
                PurchaseOrder.status.in_(["DRAFT", "APPROVED", "ORDERED", "PARTIAL"]),
            )
        )
        if po_number:
            query = query.where(PurchaseOrder.po_number == po_number)
        query = query.order_by(PurchaseOrder.order_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_pos(
        self,
        skip: int = 0,
        limit: int = 100,
        vendor_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> List[PurchaseOrder]:
        """Get a list of purchase orders."""
        query = select(PurchaseOrder).options(
            selectinload(PurchaseOrder.lines)
        ).where(PurchaseOrder.is_deleted == False)
        
        if vendor_id:
            query = query.where(PurchaseOrder.vendor_id == vendor_id)
        if status:
            query = query.where(PurchaseOrder.status == status)
        
        query = query.offset(skip).limit(limit).order_by(PurchaseOrder.order_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_po(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a new purchase order with lines."""
        po_dict = po_data.model_dump(exclude={"lines"})
        
        # Calculate totals from lines
        lines_data = po_dict.pop("lines", [])
        
        # Calculate line totals if not provided
        for line in lines_data:
            if "line_total" not in line or line["line_total"] is None:
                quantity = Decimal(str(line["quantity"]))
                unit_price = Decimal(str(line["unit_price"]))
                tax_rate = Decimal(str(line.get("tax_rate", "0")))
                line["line_total"] = quantity * unit_price
        
        # Calculate PO totals
        subtotal = sum(Decimal(str(line["line_total"])) for line in lines_data)
        tax_amount = sum(
            Decimal(str(line["line_total"])) * Decimal(str(line.get("tax_rate", "0")))
            for line in lines_data
        )
        
        po_dict["subtotal"] = subtotal
        po_dict["tax_amount"] = tax_amount
        po_dict["total_amount"] = subtotal + tax_amount
        
        # Create PO
        po = PurchaseOrder(**po_dict)
        self.db.add(po)
        await self.db.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data["purchase_order_id"] = po.id
            line = PurchaseOrderLine(**line_data)
            self.db.add(line)
        
        await self.db.flush()
        await self.db.refresh(po)
        return po
    
    async def update_po(
        self,
        po_id: uuid.UUID,
        po_data: PurchaseOrderUpdate,
    ) -> Optional[PurchaseOrder]:
        """Update an existing purchase order."""
        po = await self.get_po_by_id(po_id)
        if not po:
            return None
        
        update_data = po_data.model_dump(exclude_unset=True, exclude={"lines"})
        
        # Handle line updates if provided
        if "lines" in update_data and update_data["lines"] is not None:
            # Delete existing lines and create new ones
            for existing_line in po.lines:
                await self.db.delete(existing_line)
            
            lines_data = update_data.pop("lines")
            for line_data in lines_data:
                if "line_total" not in line_data or line_data["line_total"] is None:
                    quantity = Decimal(str(line_data["quantity"]))
                    unit_price = Decimal(str(line_data["unit_price"]))
                    line_data["line_total"] = quantity * unit_price
                line_data["purchase_order_id"] = po.id
                line = PurchaseOrderLine(**line_data)
                self.db.add(line)
        
        # Update PO fields
        for field, value in update_data.items():
            setattr(po, field, value)
        
        # Recalculate totals
        await self.db.flush()
        await self.db.refresh(po)
        await self._recalculate_totals(po)
        
        return po
    
    async def _recalculate_totals(self, po: PurchaseOrder) -> None:
        """Recalculate PO totals from lines."""
        lines = await self.db.execute(
            select(PurchaseOrderLine)
            .where(PurchaseOrderLine.purchase_order_id == po.id)
        )
        lines = list(lines.scalars().all())
        
        subtotal = sum(line.line_total for line in lines)
        tax_amount = sum(
            line.line_total * line.tax_rate for line in lines
        )
        
        po.subtotal = subtotal
        po.tax_amount = tax_amount
        po.total_amount = subtotal + tax_amount
        await self.db.flush()
    
    async def update_po_status(self, po_id: uuid.UUID, status: str) -> Optional[PurchaseOrder]:
        """Update PO status."""
        po = await self.get_po_by_id(po_id)
        if not po:
            return None
        po.status = status
        await self.db.flush()
        await self.db.refresh(po)
        return po
    
    async def delete_po(self, po_id: uuid.UUID) -> bool:
        """Soft delete a purchase order."""
        po = await self.get_po_by_id(po_id)
        if not po:
            return False
        
        po.is_deleted = True
        po.deleted_at = po.updated_at
        await self.db.flush()
        return True
