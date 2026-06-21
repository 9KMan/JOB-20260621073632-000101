// src/services/purchase_order.py
"""Purchase order service."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    """Purchase order business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _calculate_line_total(self, line: dict) -> Decimal:
        """Calculate line total including tax."""
        quantity = Decimal(str(line.quantity))
        unit_price = Decimal(str(line.unit_price))
        tax_rate = Decimal(str(line.get("tax_rate", "0")))
        subtotal = quantity * unit_price
        tax = subtotal * tax_rate
        return subtotal + tax
    
    def _calculate_totals(self, lines: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        """Calculate order totals."""
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        for line in lines:
            quantity = Decimal(str(line.quantity))
            unit_price = Decimal(str(line.unit_price))
            tax_rate = Decimal(str(line.get("tax_rate", "0")))
            line_subtotal = quantity * unit_price
            line_tax = line_subtotal * tax_rate
            subtotal += line_subtotal
            tax_amount += line_tax
        return subtotal, tax_amount, subtotal + tax_amount
    
    async def create_purchase_order(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a new purchase order."""
        lines_data = [line.model_dump() for line in po_data.lines]
        subtotal, tax_amount, total_amount = self._calculate_totals(lines_data)
        
        po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=po_data.supplier_id,
            supplier_name=po_data.supplier_name,
            supplier_reference=po_data.supplier_reference,
            order_date=po_data.order_date,
            expected_delivery_date=po_data.expected_delivery_date,
            currency=po_data.currency,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=po_data.notes,
            status=POStatus.DRAFT,
        )
        self.db.add(po)
        await self.db.flush()
        
        for idx, line_data in enumerate(lines_data):
            line_total = self._calculate_line_total(line_data)
            line = PurchaseOrderLine(
                purchase_order_id=po.id,
                line_number=line_data.get("line_number", idx + 1),
                sku=line_data.get("sku"),
                description=line_data["description"],
                quantity=Decimal(str(line_data["quantity"])),
                unit_of_measure=line_data.get("unit_of_measure", "EA"),
                unit_price=Decimal(str(line_data["unit_price"])),
                tax_rate=Decimal(str(line_data.get("tax_rate", "0"))),
                line_total=line_total,
            )
            self.db.add(line)
        
        await self.db.commit()
        await self.db.refresh(po)
        return po
    
    async def get_purchase_order(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get purchase order by ID."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()
    
    async def get_purchase_order_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by number."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.po_number == po_number)
        )
        return result.scalar_one_or_none()
    
    async def get_purchase_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[POStatus] = None,
    ) -> tuple[list[PurchaseOrder], int]:
        """Get purchase orders with optional filters."""
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines))
        count_query = select(func.count(PurchaseOrder.id))
        
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
            count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
        
        if status:
            query = query.where(PurchaseOrder.status == status)
            count_query = count_query.where(PurchaseOrder.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(skip).limit(limit).order_by(PurchaseOrder.created_at.desc())
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total
    
    async def update_purchase_order(
        self,
        po_id: UUID,
        po_data: PurchaseOrderUpdate,
    ) -> Optional[PurchaseOrder]:
        """Update a purchase order."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return None
        
        update_data = po_data.model_dump(exclude_unset=True)
        
        if "lines" in update_data:
            lines_data = update_data.pop("lines")
            for line in po.lines:
                await self.db.delete(line)
            await self.db.flush()
            
            subtotal, tax_amount, total_amount = self._calculate_totals(lines_data)
            update_data["subtotal"] = subtotal
            update_data["tax_amount"] = tax_amount
            update_data["total_amount"] = total_amount
            
            for idx, line_data in enumerate(lines_data):
                line_total = self._calculate_line_total(line_data)
                line = PurchaseOrderLine(
                    purchase_order_id=po.id,
                    line_number=line_data.get("line_number", idx + 1),
                    sku=line_data.get("sku"),
                    description=line_data["description"],
                    quantity=Decimal(str(line_data["quantity"])),
                    unit_of_measure=line_data.get("unit_of_measure", "EA"),
                    unit_price=Decimal(str(line_data["unit_price"])),
                    tax_rate=Decimal(str(line_data.get("tax_rate", "0"))),
                    line_total=line_total,
                )
                self.db.add(line)
        
        for field, value in update_data.items():
            setattr(po, field, value)
        
        await self.db.commit()
        await self.db.refresh(po)
        return po
    
    async def update_po_status(self, po_id: UUID, status: POStatus) -> Optional[PurchaseOrder]:
        """Update purchase order status."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return None
        po.status = status
        await self.db.commit()
        await self.db.refresh(po)
        return po
    
    async def update_line_quantities(
        self,
        po_id: UUID,
        line_id: UUID,
        received_qty: Optional[Decimal] = None,
        invoiced_qty: Optional[Decimal] = None,
    ) -> Optional[PurchaseOrderLine]:
        """Update line quantities for matching."""
        result = await self.db.execute(
            select(PurchaseOrderLine).where(
                PurchaseOrderLine.id == line_id,
                PurchaseOrderLine.purchase_order_id == po_id,
            )
        )
        line = result.scalar_one_or_none()
        if not line:
            return None
        
        if received_qty is not None:
            line.received_quantity = received_qty
        if invoiced_qty is not None:
            line.invoiced_quantity = invoiced_qty
        
        await self.db.commit()
        await self.db.refresh(line)
        return line
    
    async def delete_purchase_order(self, po_id: UUID) -> bool:
        """Delete a purchase order."""
        po = await self.get_purchase_order(po_id)
        if not po:
            return False
        await self.db.delete(po)
        await self.db.commit()
        return True
