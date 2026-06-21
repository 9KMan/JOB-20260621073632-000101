// src/services/delivery_note_service.py
"""Delivery Note service."""
import uuid
import decimal
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.models.enums import DocumentStatus
from src.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate


class DeliveryNoteService:
    """Service for Delivery Note operations."""

    @staticmethod
    def calculate_totals(lines: List[dict]) -> tuple[decimal.Decimal, int]:
        """Calculate total quantity and line count from lines."""
        total_quantity = decimal.Decimal("0.0000")
        total_lines = 0
        
        for line in lines:
            total_quantity += decimal.Decimal(str(line.get("quantity_delivered", 0)))
            total_lines += 1
        
        return total_quantity, total_lines

    @staticmethod
    def create_delivery_note(db: Session, dn_data: DeliveryNoteCreate) -> DeliveryNote:
        """Create a new Delivery Note with lines."""
        total_quantity = dn_data.total_quantity
        total_lines = dn_data.total_lines

        if dn_data.lines:
            total_quantity, total_lines = DeliveryNoteService.calculate_totals(
                [line.model_dump() for line in dn_data.lines]
            )

        dn = DeliveryNote(
            dn_number=dn_data.dn_number,
            supplier_id=dn_data.supplier_id,
            supplier_name=dn_data.supplier_name,
            supplier_reference=dn_data.supplier_reference,
            purchase_order_id=dn_data.purchase_order_id,
            delivery_date=dn_data.delivery_date,
            received_by=dn_data.received_by,
            total_quantity=total_quantity,
            total_lines=total_lines,
            status=dn_data.status,
            notes=dn_data.notes,
            metadata=dn_data.metadata,
        )
        db.add(dn)
        db.flush()

        for line_data in dn_data.lines:
            quantity_accepted = line_data.quantity_accepted or line_data.quantity_delivered
            
            line = DeliveryNoteLine(
                delivery_note_id=dn.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity_delivered=line_data.quantity_delivered,
                quantity_accepted=quantity_accepted,
                quantity_rejected=line_data.quantity_rejected,
                unit_of_measure=line_data.unit_of_measure,
                notes=line_data.notes,
            )
            db.add(line)

        db.commit()
        db.refresh(dn)
        return dn

    @staticmethod
    def get_delivery_note(db: Session, dn_id: uuid.UUID) -> Optional[DeliveryNote]:
        """Get a Delivery Note by ID."""
        return (
            db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .filter(DeliveryNote.id == dn_id)
            .first()
        )

    @staticmethod
    def get_delivery_note_by_number(db: Session, dn_number: str) -> Optional[DeliveryNote]:
        """Get a Delivery Note by DN number."""
        return (
            db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .filter(DeliveryNote.dn_number == dn_number)
            .first()
        )

    @staticmethod
    def get_delivery_notes(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[DocumentStatus] = None,
        po_id: Optional[uuid.UUID] = None,
    ) -> List[DeliveryNote]:
        """Get a list of Delivery Notes with optional filtering."""
        query = db.query(DeliveryNote).options(joinedload(DeliveryNote.lines))
        
        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)
        if status:
            query = query.filter(DeliveryNote.status == status)
        if po_id:
            query = query.filter(DeliveryNote.purchase_order_id == po_id)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_delivery_note(
        db: Session,
        dn: DeliveryNote,
        dn_data: DeliveryNoteUpdate,
    ) -> DeliveryNote:
        """Update a Delivery Note."""
        update_data = dn_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(dn, key, value)
        
        db.commit()
        db.refresh(dn)
        return dn

    @staticmethod
    def delete_delivery_note(db: Session, dn: DeliveryNote) -> None:
        """Soft delete a Delivery Note."""
        dn.is_deleted = True
        dn.deleted_at = date.today()
        dn.status = DocumentStatus.CANCELLED
        db.commit()

    @staticmethod
    def update_status(db: Session, dn: DeliveryNote, status: DocumentStatus) -> DeliveryNote:
        """Update a Delivery Note status."""
        dn.status = status
        db.commit()
        db.refresh(dn)
        return dn

    @staticmethod
    def get_unmatched_delivery_notes(
        db: Session,
        supplier_id: Optional[str] = None,
    ) -> List[DeliveryNote]:
        """Get delivery notes that haven't been fully matched."""
        query = (
            db.query(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .filter(
                DeliveryNote.is_deleted == False,
                DeliveryNote.status.in_([
                    DocumentStatus.SUBMITTED,
                    DocumentStatus.PARTIALLY_MATCHED,
                ])
            )
        )
        
        if supplier_id:
            query = query.filter(DeliveryNote.supplier_id == supplier_id)
        
        return query.all()
