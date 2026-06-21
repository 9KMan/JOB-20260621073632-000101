# src/services/delivery_note.py
"""Delivery Note service."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate


class DeliveryNoteService:
    """Service for delivery note management."""

    def __init__(self, db: Session):
        """Initialize delivery note service with database session."""
        self.db = db

    def get_by_id(self, dn_id: UUID) -> Optional[DeliveryNote]:
        """Get delivery note by ID with line items."""
        return (
            self.db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.line_items))
            .filter(DeliveryNote.id == dn_id)
            .first()
        )

    def get_by_dn_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get delivery note by DN number."""
        return (
            self.db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.line_items))
            .filter(DeliveryNote.dn_number == dn_number)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        purchase_order_id: Optional[UUID] = None,
    ) -> List[DeliveryNote]:
        """Get all delivery notes with pagination and filters."""
        query = self.db.query(DeliveryNote).options(joinedload(DeliveryNote.line_items))

        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)
        if status:
            query = query.filter(DeliveryNote.status == status)
        if purchase_order_id:
            query = query.filter(DeliveryNote.purchase_order_id == purchase_order_id)

        return query.order_by(DeliveryNote.created_at.desc()).offset(skip).limit(limit).all()

    def get_total_count(
        self,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        purchase_order_id: Optional[UUID] = None,
    ) -> int:
        """Get total count of delivery notes with filters."""
        query = self.db.query(DeliveryNote)

        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)
        if status:
            query = query.filter(DeliveryNote.status == status)
        if purchase_order_id:
            query = query.filter(DeliveryNote.purchase_order_id == purchase_order_id)

        return query.count()

    def create(self, dn_data: DeliveryNoteCreate) -> DeliveryNote:
        """Create new delivery note with line items."""
        # Calculate total from line items if not provided
        total_amount = dn_data.total_amount
        if dn_data.line_items:
            total_amount = sum(line.line_amount for line in dn_data.line_items)

        dn = DeliveryNote(
            dn_number=dn_data.dn_number,
            supplier_id=dn_data.supplier_id,
            supplier_name=dn_data.supplier_name,
            dn_date=dn_data.dn_date,
            received_date=dn_data.received_date,
            total_amount=total_amount,
            currency=dn_data.currency,
            status=dn_data.status,
            notes=dn_data.notes,
            purchase_order_id=dn_data.purchase_order_id,
        )
        self.db.add(dn)
        self.db.flush()

        # Add line items
        for line_data in dn_data.line_items:
            line = DeliveryNoteLine(
                delivery_note_id=dn.id,
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
        self.db.refresh(dn)
        return self.get_by_id(dn.id)

    def update(
        self,
        dn_id: UUID,
        dn_data: DeliveryNoteUpdate,
    ) -> Optional[DeliveryNote]:
        """Update existing delivery note."""
        dn = self.get_by_id(dn_id)
        if not dn:
            return None

        update_data = dn_data.model_dump(exclude_unset=True, exclude={"line_items"})

        for field, value in update_data.items():
            setattr(dn, field, value)

        # Update line items if provided
        if dn_data.line_items is not None:
            # Remove existing lines
            self.db.query(DeliveryNoteLine).filter(
                DeliveryNoteLine.delivery_note_id == dn_id
            ).delete()

            # Add new lines
            for line_data in dn_data.line_items:
                line = DeliveryNoteLine(
                    delivery_note_id=dn_id,
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
            dn.total_amount = sum(line.line_amount for line in dn_data.line_items)

        self.db.commit()
        self.db.refresh(dn)
        return self.get_by_id(dn_id)

    def update_status(self, dn_id: UUID, status: str) -> Optional[DeliveryNote]:
        """Update delivery note status."""
        dn = self.get_by_id(dn_id)
        if not dn:
            return None

        dn.status = status
        self.db.commit()
        self.db.refresh(dn)
        return dn

    def delete(self, dn_id: UUID) -> bool:
        """Delete delivery note."""
        dn = self.get_by_id(dn_id)
        if not dn:
            return False

        self.db.delete(dn)
        self.db.commit()
        return True

    def get_unmatched_delivery_notes(
        self, supplier_id: Optional[str] = None
    ) -> List[DeliveryNote]:
        """Get delivery notes that haven't been matched yet."""
        query = (
            self.db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.line_items))
            .filter(DeliveryNote.status == "pending")
        )

        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)

        return query.all()
