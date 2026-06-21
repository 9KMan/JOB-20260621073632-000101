// src/services/purchase_order_service.py
"""Purchase Order service for business logic."""
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.models.supplier import Supplier
from src.services.base import BaseService


class PurchaseOrderService(BaseService[PurchaseOrder]):
    """Service for Purchase Order operations."""

    def __init__(self, db: Session):
        """Initialize PO service."""
        super().__init__(PurchaseOrder, db)

    def get_with_lines(self, id: UUID) -> Optional[PurchaseOrder]:
        """Get PO with lines eagerly loaded."""
        stmt = (
            select(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .options(joinedload(PurchaseOrder.supplier))
            .where(
                PurchaseOrder.id == id,
                PurchaseOrder.is_deleted == False,  # noqa: E712
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get PO by PO number."""
        return self.get_by_field("po_number", po_number)

    def get_open_pos_for_supplier(self, supplier_id: UUID) -> List[PurchaseOrder]:
        """Get all open POs for a supplier (for anchoring)."""
        stmt = (
            select(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .where(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_([
                    POStatus.SUBMITTED,
                    POStatus.APPROVED,
                    POStatus.PARTIALLY_RECEIVED,
                ]),
                PurchaseOrder.is_deleted == False,  # noqa: E712
            )
            .order_by(PurchaseOrder.order_date.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def find_po_by_reference(
        self, supplier_id: UUID, po_reference: str
    ) -> Optional[PurchaseOrder]:
        """Find PO by supplier and PO reference number."""
        stmt = (
            select(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .where(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.po_number == po_reference,
                PurchaseOrder.is_deleted == False,  # noqa: E712
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create(self, data: dict) -> PurchaseOrder:
        """Create a new PO with lines."""
        lines_data = data.pop("lines", [])
        
        # Calculate totals
        subtotal = sum(Decimal(str(line.get("line_total", 0))) for line in lines_data)
        tax_amount = sum(Decimal(str(line.get("tax_amount", 0))) for line in lines_data)
        total_amount = subtotal + tax_amount

        po_data = {
            **data,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        }

        po = PurchaseOrder(**po_data)
        self.db.add(po)
        self.db.flush()

        # Create lines
        for line_data in lines_data:
            line_data["po_id"] = po.id
            line = PurchaseOrderLine(**line_data)
            self.db.add(line)

        self.db.flush()
        self.db.refresh(po)
        return po

    def update(self, id: UUID, data: dict) -> Optional[PurchaseOrder]:
        """Update a PO."""
        po = self.get(id)
        if po:
            lines_data = data.pop("lines", None)
            
            for field, value in data.items():
                if hasattr(po, field) and value is not None:
                    setattr(po, field, value)

            if lines_data is not None:
                # Update lines
                for line_data in lines_data:
                    line_id = line_data.pop("id", None)
                    if line_id:
                        line = self.db.get(PurchaseOrderLine, line_id)
                        if line:
                            for field, value in line_data.items():
                                if hasattr(line, field) and value is not None:
                                    setattr(line, field, value)
                    else:
                        line_data["po_id"] = po.id
                        line = PurchaseOrderLine(**line_data)
                        self.db.add(line)

            self.db.flush()
            self.db.refresh(po)
        return po

    def update_status(self, id: UUID, status: POStatus) -> Optional[PurchaseOrder]:
        """Update PO status."""
        return self.update(id, {"status": status.value if isinstance(status, POStatus) else status})

    def update_received_quantity(
        self, po_line_id: UUID, received_qty: Decimal
    ) -> Optional[PurchaseOrderLine]:
        """Update received quantity for a PO line."""
        line = self.db.get(PurchaseOrderLine, po_line_id)
        if line:
            line.received_quantity = received_qty
            self.db.flush()
            self.db.refresh(line)
        return line

    def get_multi_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[PurchaseOrder], int]:
        """Get POs with pagination and filters."""
        stmt = (
            select(PurchaseOrder)
            .options(joinedload(PurchaseOrder.supplier))
            .options(joinedload(PurchaseOrder.lines))
            .where(PurchaseOrder.is_deleted == False)  # noqa: E712
        )

        if supplier_id:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)

        if status:
            stmt = stmt.where(PurchaseOrder.status == status)

        if search:
            stmt = stmt.where(PurchaseOrder.po_number.ilike(f"%{search}%"))

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar()

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size).order_by(PurchaseOrder.created_at.desc())

        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total
