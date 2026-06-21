// src/services/purchase_order_service.py
"""Purchase Order service for PO management."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate
from src.services.base import BaseService
from src.services.audit_service import AuditService


class PurchaseOrderService(BaseService[PurchaseOrder]):
    """Service for Purchase Order management."""

    def __init__(self, db: Session):
        """Initialize PO service."""
        super().__init__(PurchaseOrder, db)
        self.audit_service = AuditService(db)

    def get_by_po_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get PO by PO number."""
        return (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.po_number == po_number)
            .first()
        )

    def get_by_supplier(self, supplier_id: str, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
        """Get POs by supplier."""
        return (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_open_pos(self, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
        """Get all open POs."""
        return (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.status.in_(["open", "partial"]))
            .options(joinedload(PurchaseOrder.lines))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_po_number_and_supplier(self, po_number: str, supplier_id: str) -> Optional[PurchaseOrder]:
        """Get PO by number and supplier for anchoring."""
        return (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.po_number == po_number,
                PurchaseOrder.supplier_id == supplier_id,
            )
            .options(joinedload(PurchaseOrder.lines))
            .first()
        )

    def create_po(self, po_data: PurchaseOrderCreate, created_by: Optional[str] = None) -> PurchaseOrder:
        """Create a new Purchase Order with lines."""
        # Check for duplicate
        existing = self.get_by_po_number(po_data.po_number)
        if existing:
            raise ValueError(f"PO with number {po_data.po_number} already exists")

        # Calculate totals
        subtotal = sum(line.line_total for line in po_data.lines)
        tax_amount = sum(line.tax_amount for line in po_data.lines)
        total_amount = subtotal + tax_amount

        # Create PO data
        po_dict = po_data.model_dump(exclude={"lines"})
        po_dict["subtotal"] = subtotal
        po_dict["tax_amount"] = tax_amount
        po_dict["total_amount"] = total_amount
        if created_by:
            po_dict["created_by"] = created_by

        # Create PO with lines
        po = PurchaseOrder(**po_dict)
        self.db.add(po)
        self.db.flush()  # Get PO ID

        # Create lines
        for line_data in po_data.lines:
            line_dict = line_data.model_dump()
            line = PurchaseOrderLine(purchase_order_id=po.id, **line_dict)
            self.db.add(line)

        self.db.commit()
        self.db.refresh(po)

        # Audit log
        self.audit_service.log_create(po, created_by)

        return po

    def update_po(self, id: str, po_data: PurchaseOrderUpdate) -> Optional[PurchaseOrder]:
        """Update Purchase Order."""
        po = self.get_by_id(id)
        if not po:
            return None

        update_dict = po_data.model_dump(exclude_unset=True)
        
        # Audit before update
        self.audit_service.log_update(po, update_dict, po.created_by)

        return self.update(id, update_dict)

    def close_po(self, id: str) -> Optional[PurchaseOrder]:
        """Close a PO."""
        po = self.get_by_id(id)
        if po:
            po.status = "closed"
            self.db.commit()
            self.db.refresh(po)
            self.audit_service.log_update(
                po, {"status": "closed"}, po.created_by
            )
        return po

    def update_po_totals(self, po: PurchaseOrder) -> PurchaseOrder:
        """Recalculate and update PO totals."""
        # Recalculate from lines
        subtotal = sum(Decimal(str(line.line_total)) for line in po.lines)
        tax_amount = sum(Decimal(str(line.tax_amount)) for line in po.lines)
        total_received = sum(Decimal(str(line.quantity_received)) for line in po.lines)
        total_invoiced = sum(Decimal(str(line.quantity_invoiced)) for line in po.lines)

        po.subtotal = subtotal
        po.tax_amount = tax_amount
        po.total_amount = subtotal + tax_amount
        po.total_received = total_received
        po.total_invoiced = total_invoiced

        # Update status based on received/invoiced amounts
        if po.total_received >= po.total_amount or po.total_invoiced >= po.total_amount:
            po.status = "closed"
        elif po.total_received > 0 or po.total_invoiced > 0:
            po.status = "partial"

        self.db.commit()
        self.db.refresh(po)
        return po

    def update_line_received(self, po_line_id: str, quantity: Decimal) -> Optional[PurchaseOrderLine]:
        """Update received quantity on PO line."""
        line = self.db.query(PurchaseOrderLine).filter(PurchaseOrderLine.id == po_line_id).first()
        if line:
            line.quantity_received = quantity
            self.db.commit()
            self.db.refresh(line)
        return line

    def update_line_invoiced(self, po_line_id: str, quantity: Decimal) -> Optional[PurchaseOrderLine]:
        """Update invoiced quantity on PO line."""
        line = self.db.query(PurchaseOrderLine).filter(PurchaseOrderLine.id == po_line_id).first()
        if line:
            line.quantity_invoiced = quantity
            self.db.commit()
            self.db.refresh(line)
        return line

    def get_line_by_id(self, line_id: str) -> Optional[PurchaseOrderLine]:
        """Get PO line by ID."""
        return self.db.query(PurchaseOrderLine).filter(PurchaseOrderLine.id == line_id).first()
