// src/services/purchase_order_service.py
"""Purchase Order service."""
import uuid
import decimal
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.models.enums import DocumentStatus
from src.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate


class PurchaseOrderService:
    """Service for Purchase Order operations."""

    @staticmethod
    def calculate_totals(lines: List[dict]) -> decimal.Decimal:
        """Calculate total amount from lines."""
        return sum(
            (decimal.Decimal(str(line.get("line_amount", 0))) for line in lines),
            decimal.Decimal("0.00")
        )

    @staticmethod
    def create_purchase_order(db: Session, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create a new Purchase Order with lines."""
        total_amount = po_data.total_amount
        if po_data.lines:
            total_amount = PurchaseOrderService.calculate_totals(
                [line.model_dump() for line in po_data.lines]
            )

        po = PurchaseOrder(
            po_number=po_data.po_number,
            supplier_id=po_data.supplier_id,
            supplier_name=po_data.supplier_name,
            supplier_reference=po_data.supplier_reference,
            order_date=po_data.order_date,
            expected_delivery_date=po_data.expected_delivery_date,
            total_amount=total_amount,
            currency=po_data.currency,
            status=po_data.status,
            notes=po_data.notes,
            metadata=po_data.metadata,
        )
        db.add(po)
        db.flush()

        for line_data in po_data.lines:
            line = PurchaseOrderLine(
                purchase_order_id=po.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                line_amount=line_data.line_amount,
                tax_rate=line_data.tax_rate,
                tax_amount=line_data.tax_amount,
                expected_delivery_date=line_data.expected_delivery_date,
                notes=line_data.notes,
            )
            db.add(line)

        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def get_purchase_order(db: Session, po_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """Get a Purchase Order by ID."""
        return (
            db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

    @staticmethod
    def get_purchase_order_by_number(db: Session, po_number: str) -> Optional[PurchaseOrder]:
        """Get a Purchase Order by PO number."""
        return (
            db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .filter(PurchaseOrder.po_number == po_number)
            .first()
        )

    @staticmethod
    def get_purchase_orders(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[DocumentStatus] = None,
    ) -> List[PurchaseOrder]:
        """Get a list of Purchase Orders with optional filtering."""
        query = db.query(PurchaseOrder).options(joinedload(PurchaseOrder.lines))
        
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_purchase_order(
        db: Session,
        po: PurchaseOrder,
        po_data: PurchaseOrderUpdate,
    ) -> PurchaseOrder:
        """Update a Purchase Order."""
        update_data = po_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(po, key, value)
        
        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def delete_purchase_order(db: Session, po: PurchaseOrder) -> None:
        """Soft delete a Purchase Order."""
        po.is_deleted = True
        po.deleted_at = date.today()
        po.status = DocumentStatus.CANCELLED
        db.commit()

    @staticmethod
    def update_status(db: Session, po: PurchaseOrder, status: DocumentStatus) -> PurchaseOrder:
        """Update a Purchase Order status."""
        po.status = status
        db.commit()
        db.refresh(po)
        return po

    @staticmethod
    def get_open_pos_by_supplier(
        db: Session,
        supplier_id: str,
    ) -> List[PurchaseOrder]:
        """Get open (unmatched) POs for a supplier."""
        return (
            db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .filter(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.is_deleted == False,
                PurchaseOrder.status.in_([
                    DocumentStatus.SUBMITTED,
                    DocumentStatus.APPROVED,
                    DocumentStatus.PARTIALLY_MATCHED,
                ])
            )
            .all()
        )
