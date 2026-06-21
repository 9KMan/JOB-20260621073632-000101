// src/app/services/purchase_order_service.py
"""Purchase Order service."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.app.models.base import BaseModel
from src.app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderLineResponse,
    PurchaseOrderSummary,
)


class PurchaseOrderService:
    """Service for Purchase Order operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_purchase_order(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a new purchase order with lines."""
        po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=uuid.UUID(po_data.supplier_id),
            supplier_name=po_data.supplier_name,
            supplier_code=po_data.supplier_code,
            order_date=po_data.order_date,
            expected_delivery_date=po_data.expected_delivery_date,
            delivery_address=po_data.delivery_address,
            currency=po_data.currency,
            status=po_data.status or POStatus.DRAFT.value,
            notes=po_data.notes,
        )
        
        self.db.add(po)
        await self.db.flush()
        
        for line_data in po_data.lines:
            line = PurchaseOrderLine(
                purchase_order_id=po.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                product_name=line_data.product_name,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                tax_code=line_data.tax_code,
                tax_rate=line_data.tax_rate,
                expected_delivery_date=line_data.expected_delivery_date,
                notes=line_data.notes,
            )
            line.line_amount = line_data.quantity * line_data.unit_price * (1 + line_data.tax_rate / 100)
            self.db.add(line)
        
        await self.db.flush()
        await self._recalculate_totals(po.id)
        await self.db.refresh(po)
        
        return po
    
    async def get_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        """Get a purchase order by ID."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == uuid.UUID(po_id))
        )
        return result.scalar_one_or_none()
    
    async def get_purchase_order_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get a purchase order by PO number."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.po_number == po_number)
        )
        return result.scalar_one_or_none()
    
    async def list_purchase_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_code: Optional[str] = None,
        status: Optional[str] = None,
        is_archived: bool = False,
    ) -> tuple[list[PurchaseOrder], int]:
        """List purchase orders with pagination and filters."""
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
        
        if supplier_code:
            query = query.where(PurchaseOrder.supplier_code == supplier_code)
        if status:
            query = query.where(PurchaseOrder.status == status)
        if is_archived is not None:
            query = query.where(PurchaseOrder.is_archived == is_archived)
        
        count_query = select(func.count(PurchaseOrder.id))
        if supplier_code:
            count_query = count_query.where(PurchaseOrder.supplier_code == supplier_code)
        if status:
            count_query = count_query.where(PurchaseOrder.status == status)
        if is_archived is not None:
            count_query = count_query.where(PurchaseOrder.is_archived == is_archived)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(PurchaseOrder.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        purchase_orders = result.scalars().all()
        
        return list(purchase_orders), total
    
    async def update_purchase_order(
        self,
        po_id: str,
        po_data: PurchaseOrderUpdate,
    ) -> Optional[PurchaseOrder]:
        """Update a purchase order."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return None
        
        update_data = po_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(po, field, value)
        
        await self.db.flush()
        await self.db.refresh(po)
        return po
    
    async def delete_purchase_order(self, po_id: str) -> bool:
        """Delete a purchase order."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return False
        
        await self.db.delete(po)
        await self.db.flush()
        return True
    
    async def archive_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        """Archive a purchase order."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return None
        
        po.is_archived = True
        await self.db.flush()
        await self.db.refresh(po)
        return po
    
    async def close_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        """Close a purchase order."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return None
        
        po.status = POStatus.CLOSED.value
        await self.db.flush()
        await self.db.refresh(po)
        return po
    
    async def get_open_purchase_orders(
        self,
        supplier_code: Optional[str] = None,
    ) -> list[PurchaseOrder]:
        """Get all open (unfulfilled) purchase orders."""
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines)).where(
            PurchaseOrder.status.in_([POStatus.SUBMITTED.value, POStatus.APPROVED.value]),
            PurchaseOrder.is_archived == False,
        )
        
        if supplier_code:
            query = query.where(PurchaseOrder.supplier_code == supplier_code)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_po_summary(self, po_id: str) -> Optional[PurchaseOrderSummary]:
        """Get purchase order summary for matching."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return None
        
        return PurchaseOrderSummary(
            id=str(po.id),
            po_number=po.po_number,
            supplier_code=po.supplier_code,
            total_amount=po.total_amount,
            currency=po.currency,
            status=po.status,
            open_amount=po.total_amount,
            line_count=len(po.lines),
        )
    
    async def _recalculate_totals(self, po_id: uuid.UUID) -> None:
        """Recalculate PO totals from lines."""
        result = await self.db.execute(
            select(
                func.sum(PurchaseOrderLine.line_amount).label("subtotal"),
                func.sum(PurchaseOrderLine.line_amount * PurchaseOrderLine.tax_rate / 100).label("tax"),
            )
            .where(PurchaseOrderLine.purchase_order_id == po_id)
        )
        row = result.one()
        
        subtotal = row.subtotal or Decimal("0.00")
        tax = row.tax or Decimal("0.00")
        
        await self.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        )
        po_result = await self.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        )
        po = po_result.scalar_one()
        po.subtotal = subtotal
        po.tax_amount = tax
        po.total_amount = subtotal + tax
        await self.db.flush()
