// src/services/purchase_order_service.py
"""Purchase Order service."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session, joinedload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.models.supplier import Supplier
from src.models.enums import DocumentStatus
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate
from src.services.base_service import BaseService


class PurchaseOrderService(BaseService[PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate]):
    """Service for Purchase Order operations."""
    
    def __init__(self, db: Session):
        super().__init__(PurchaseOrder, db)
    
    def _calculate_totals(self, lines_data: List[dict]) -> tuple[Decimal, Decimal, Decimal]:
        """Calculate subtotal, tax, and total from lines."""
        subtotal = sum(Decimal(str(line.get('line_amount', 0))) for line in lines_data)
        # Assuming 10% tax rate for calculation
        tax_amount = subtotal * Decimal("0.10")
        total = subtotal + tax_amount
        return subtotal, tax_amount, total
    
    def create_po(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """
        Create a new Purchase Order with lines.
        
        Args:
            po_data: PO creation data
            
        Returns:
            Created PO with lines
        """
        # Extract lines data
        lines_data = [line.model_dump() for line in po_data.lines]
        
        # Calculate totals if not provided
        if po_data.subtotal is None:
            subtotal, tax_amount, total = self._calculate_totals(lines_data)
        else:
            subtotal = po_data.subtotal
            tax_amount = po_data.tax_amount or Decimal("0.00")
            total = po_data.total_amount or subtotal + tax_amount
        
        # Create PO
        db_po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=po_data.supplier_id,
            order_date=po_data.order_date,
            expected_delivery_date=po_data.expected_delivery_date,
            status=DocumentStatus.DRAFT,
            currency=po_data.currency,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total,
            notes=po_data.notes,
        )
        self.db.add(db_po)
        self.db.flush()  # Get the ID
        
        # Create lines
        for line_data in lines_data:
            line_data.pop('id', None)  # Remove id if present
            po_line = PurchaseOrderLine(
                purchase_order_id=db_po.id,
                **line_data
            )
            self.db.add(po_line)
        
        # Update status to OPEN
        db_po.status = DocumentStatus.OPEN
        self.db.commit()
        self.db.refresh(db_po)
        return db_po
    
    def get_po_with_lines(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get a PO with its lines eagerly loaded."""
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(
            PurchaseOrder.id == po_id,
            PurchaseOrder.is_deleted == False
        ).first()
    
    def get_po_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        """Get a PO by its number."""
        return self.get_by(po_number=po_number)
    
    def get_open_pos_by_supplier(self, supplier_id: UUID) -> List[PurchaseOrder]:
        """Get all open POs for a supplier."""
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status == DocumentStatus.OPEN,
            PurchaseOrder.is_deleted == False
        ).all()
    
    def get_pos_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[PurchaseOrder]:
        """Get POs within a date range."""
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.is_deleted == False
        ).all()
    
    def update_po(
        self,
        po_id: UUID,
        update_data: PurchaseOrderUpdate
    ) -> Optional[PurchaseOrder]:
        """Update a Purchase Order."""
        return self.update(po_id, update_data)
    
    def update_po_status(
        self,
        po_id: UUID,
        status: DocumentStatus
    ) -> Optional[PurchaseOrder]:
        """Update PO status."""
        po = self.get(po_id)
        if po:
            po.status = status
            self.db.commit()
            self.db.refresh(po)
        return po
