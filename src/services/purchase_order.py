# src/services/purchase_order.py
"""Purchase Order service."""
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    """Service for purchase order management."""

    def __init__(self, db: Session):
        """Initialize purchase order service with database session."""
        self.db = db

    def get_by_id(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get purchase order by ID with line items."""
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.line_items))
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

    def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by PO number."""
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.line_items))
            .filter(PurchaseOrder.po_number == po_number)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[PurchaseOrder]:
        """Get all purchase orders with pagination and filters."""
        query = self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.line_items))

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)

        return query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()

    def get_total_count(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Get total count of purchase orders with filters."""
        query = self.db.query(PurchaseOrder)

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)

        return query.count()

    def create(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create new purchase order with line items."""
        # Calculate total from line items if not provided
        total_amount = po_data.total_amount
        if po_data.line_items:
            total_amount = sum(line.line_amount for line in po_data.line_items)

        po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=po_data.supplier_id,
            supplier_name=po_data.supplier_name,
            po_date=po_data.po_date,
            expected_delivery_date=po_data.expected_delivery_date,
            total_amount=total_amount,
            currency=po_data.currency,
            status=po_data.status,
            notes=po_data.notes,
        )
        self.db.add(po)
        self.db.flush()

        # Add line items
        for line_data in po_data.line_items:
            line = PurchaseOrderLine(
                purchase_order_id=po.id,
                line_number=line_data.line_number,
                item_code=line_data.item_code,
                item_description=line_data.item_description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                line_amount=line_data.line_amount,
                uom=line_data.uom,
            )
            self.db.add(line)

        self.db.commit()
        self.db.refresh(po)
        return self.get_by_id(po.id)

    def update(
        self,
        po_id: UUID,
        po_data: PurchaseOrderUpdate,
    ) -> Optional[PurchaseOrder]:
        """Update existing purchase order."""
        po = self.get_by_id(po_id)
        if not po:
            return None

        update_data = po_data.model_dump(exclude_unset=True, exclude={"line_items"})

        for field, value in update_data.items():
            setattr(po, field, value)

        # Update line items if provided
        if po_data.line_items is not None:
            # Remove existing lines
            self.db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.purchase_order_id == po_id
            ).delete()

            # Add new lines
            for line_data in po_data.line_items:
                line = PurchaseOrderLine(
                    purchase_order_id=po_id,
                    line_number=line_data.line_number,
                    item_code=line_data.item_code,
                    item_description=line_data.item_description,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    line_amount=line_data.line_amount,
                    uom=line_data.uom,
                )
                self.db.add(line)

            # Recalculate total
            total = sum(line.line_amount for line in po_data.line_items)
            po.total_amount = total

        self.db.commit()
        self.db.refresh(po)
        return self.get_by_id(po_id)

    def update_status(self, po_id: UUID, status: str) -> Optional[PurchaseOrder]:
        """Update purchase order status."""
        po = self.get_by_id(po_id)
        if not po:
            return None

        po.status = status
        self.db.commit()
        self.db.refresh(po)
        return po

    def delete(self, po_id: UUID) -> bool:
        """Delete purchase order."""
        po = self.get_by_id(po_id)
        if not po:
            return False

        self.db.delete(po)
        self.db.commit()
        return True

    def get_open_pos_by_supplier(self, supplier_id: str) -> List[PurchaseOrder]:
        """Get all open purchase orders for a supplier."""
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.line_items))
            .filter(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status == "open",
            )
            .all()
        )
