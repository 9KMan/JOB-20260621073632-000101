# src/services/purchase_order_service.py
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    """Service for Purchase Order operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, po_id: str) -> Optional[PurchaseOrder]:
        """Get PO by ID with lines."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get PO by number."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.po_number == po_number)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[POStatus] = None
    ) -> List[PurchaseOrder]:
        """Get all POs with pagination and optional status filter."""
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))

        if status:
            query = query.where(PurchaseOrder.status == status)

        result = await self.db.execute(
            query.offset(skip).limit(limit).order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_supplier(
        self, supplier_id: str, skip: int = 0, limit: int = 100
    ) -> List[PurchaseOrder]:
        """Get POs by supplier."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .order_by(PurchaseOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_open_pos(self, supplier_id: Optional[str] = None) -> List[PurchaseOrder]:
        """Get open POs for matching."""
        query = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.status == POStatus.OPEN)
        )

        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)

        result = await self.db.execute(query.order_by(PurchaseOrder.order_date))
        return list(result.scalars().all())

    async def create(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a new PO with lines."""
        # Calculate totals
        total_amount = Decimal("0")
        tax_amount = Decimal("0")

        for line in po_data.lines:
            line_amount = line.quantity * line.unit_price
            line_tax = line_amount * line.tax_rate if line.tax_rate else Decimal("0")
            total_amount += line_amount + line_tax
            tax_amount += line_tax

        po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=po_data.supplier_id,
            supplier_name=po_data.supplier_name,
            supplier_code=po_data.supplier_code,
            order_date=po_data.order_date,
            expected_delivery_date=po_data.expected_delivery_date,
            currency=po_data.currency,
            total_amount=total_amount,
            tax_amount=tax_amount,
            notes=po_data.notes,
            metadata=po_data.metadata,
            status=POStatus.OPEN,
        )
        self.db.add(po)
        await self.db.flush()

        # Create lines
        for line_data in po_data.lines:
            line_amount = line_data.quantity * line_data.unit_price
            line_tax = line_amount * (line_data.tax_rate or Decimal("0"))

            po_line = PurchaseOrderLine(
                purchase_order_id=po.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                product_name=line_data.product_name,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                line_amount=line_amount,
                tax_rate=line_data.tax_rate or Decimal("0"),
                tax_amount=line_tax,
                expected_delivery_date=line_data.expected_delivery_date,
                notes=line_data.notes,
            )
            self.db.add(po_line)

        await self.db.flush()
        await self.db.refresh(po)
        return po

    async def update(self, po_id: str, po_data: PurchaseOrderUpdate) -> Optional[PurchaseOrder]:
        """Update an existing PO."""
        po = await self.get_by_id(po_id)
        if not po:
            return None

        update_data = po_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(po, field, value)

        await self.db.flush()
        await self.db.refresh(po)
        return po

    async def update_status(self, po_id: str, status: POStatus) -> Optional[PurchaseOrder]:
        """Update PO status."""
        po = await self.get_by_id(po_id)
        if not po:
            return None
        po.status = status
        await self.db.flush()
        await self.db.refresh(po)
        return po

    async def delete(self, po_id: str) -> bool:
        """Delete a PO."""
        po = await self.get_by_id(po_id)
        if not po:
            return False
        await self.db.delete(po)
        await self.db.flush()
        return True
