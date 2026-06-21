// src/services/purchase_order_service.py
"""Purchase Order service."""
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.models.enums import DocumentStatus
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    """Service for Purchase Order operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_purchase_order(
        self,
        po_data: PurchaseOrderCreate
    ) -> PurchaseOrder:
        """Create a new purchase order with lines."""
        po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=po_data.supplier_id,
            order_date=po_data.order_date,
            expected_delivery_date=po_data.expected_delivery_date,
            currency=po_data.currency,
            notes=po_data.notes,
            status=DocumentStatus.DRAFT,
        )
        
        self.db.add(po)
        await self.db.flush()  # Get the PO ID
        
        # Create lines
        for line_data in po_data.lines:
            line = PurchaseOrderLine(
                purchase_order_id=po.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                tax_rate=line_data.tax_rate,
                expected_delivery_date=line_data.expected_delivery_date,
            )
            line.calculate_totals()
            self.db.add(line)
        
        await self.db.flush()
        
        # Recalculate totals
        po.calculate_totals()
        
        await self.db.commit()
        await self.db.refresh(po)
        
        return po

    async def get_purchase_order_by_id(
        self,
        po_id: uuid.UUID,
        include_lines: bool = True
    ) -> Optional[PurchaseOrder]:
        """Get a purchase order by ID."""
        query = select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.is_deleted == False
        )
        
        if include_lines:
            query = query.options(selectinload(PurchaseOrder.lines))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_purchase_order_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get a purchase order by PO number."""
        result = await self.db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.po_number == po_number,
                PurchaseOrder.is_deleted == False
            ).options(selectinload(PurchaseOrder.lines))
        )
        return result.scalar_one_or_none()

    async def update_purchase_order(
        self,
        po_id: uuid.UUID,
        po_data: PurchaseOrderUpdate
    ) -> Optional[PurchaseOrder]:
        """Update an existing purchase order."""
        po = await self.get_purchase_order_by_id(po_id)
        if not po:
            return None
        
        update_data = po_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(po, field, value)
        
        await self.db.commit()
        await self.db.refresh(po)
        
        return po

    async def approve_purchase_order(
        self,
        po_id: uuid.UUID,
        approved_by_id: uuid.UUID
    ) -> Optional[PurchaseOrder]:
        """Approve a purchase order."""
        po = await self.get_purchase_order_by_id(po_id)
        if not po:
            return None
        
        from datetime import datetime
        po.status = DocumentStatus.APPROVED
        po.approved_at = datetime.utcnow()
        po.approved_by_id = approved_by_id
        
        await self.db.commit()
        await self.db.refresh(po)
        
        return po

    async def delete_purchase_order(self, po_id: uuid.UUID) -> bool:
        """Soft delete a purchase order."""
        po = await self.get_purchase_order_by_id(po_id)
        if not po:
            return False
        
        po.soft_delete()
        await self.db.commit()
        
        return True

    async def list_purchase_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[uuid.UUID] = None,
        status: Optional[DocumentStatus] = None,
        po_number: Optional[str] = None
    ) -> tuple[list[PurchaseOrder], int]:
        """List purchase orders with pagination and filtering."""
        query = select(PurchaseOrder).where(PurchaseOrder.is_deleted == False)
        
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.where(PurchaseOrder.status == status)
        if po_number:
            query = query.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))
        
        # Get total count
        count_query = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.is_deleted == False)
        if supplier_id:
            count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
        if status:
            count_query = count_query.where(PurchaseOrder.status == status)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get paginated results with lines
        query = query.options(
            selectinload(PurchaseOrder.lines),
            selectinload(PurchaseOrder.supplier)
        ).offset(skip).limit(limit).order_by(PurchaseOrder.order_date.desc())
        
        result = await self.db.execute(query)
        purchase_orders = result.scalars().all()
        
        return list(purchase_orders), total

    async def find_open_pos_by_supplier(
        self,
        supplier_id: uuid.UUID
    ) -> list[PurchaseOrder]:
        """Find open (approved) POs for a supplier."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .where(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status == DocumentStatus.APPROVED,
                PurchaseOrder.is_deleted == False
            )
            .options(selectinload(PurchaseOrder.lines))
            .order_by(PurchaseOrder.order_date.desc())
        )
        return list(result.scalars().all())
