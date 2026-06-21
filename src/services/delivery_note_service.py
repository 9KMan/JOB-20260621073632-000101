// src/services/delivery_note_service.py
"""Delivery Note service for DN management."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate
from src.services.base import BaseService
from src.services.audit_service import AuditService


class DeliveryNoteService(BaseService[DeliveryNote]):
    """Service for Delivery Note management."""

    def __init__(self, db: Session):
        """Initialize DN service."""
        super().__init__(DeliveryNote, db)
        self.audit_service = AuditService(db)

    def get_by_dn_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get DN by DN number."""
        return (
            self.db.query(DeliveryNote)
            .filter(DeliveryNote.dn_number == dn_number)
            .first()
        )

    def get_by_supplier(self, supplier_id: str, skip: int = 0, limit: int = 100) -> List[DeliveryNote]:
        """Get DNs by supplier."""
        return (
            self.db.query(DeliveryNote)
            .filter(DeliveryNote.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_po(self, po_id: str, skip: int = 0, limit: int = 100) -> List[DeliveryNote]:
        """Get DNs linked to a PO."""
        return (
            self.db.query(DeliveryNote)
            .filter(DeliveryNote.po_id == po_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pending_dns(self, skip: int = 0, limit: int = 100) -> List[DeliveryNote]:
        """Get all pending DNs."""
        return (
            self.db.query(DeliveryNote)
            .filter(DeliveryNote.status == "pending")
            .options(joinedload(DeliveryNote.lines))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[DeliveryNote]:
        """Get DNs by status."""
        return (
            self.db.query(DeliveryNote)
            .filter(DeliveryNote.status == status)
            .options(joinedload(DeliveryNote.lines))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_dn(self, dn_data: DeliveryNoteCreate, received_by: Optional[str] = None) -> DeliveryNote:
        """Create a new Delivery Note with lines."""
        # Check for duplicate
        existing = self.get_by_dn_number(dn_data.dn_number)
        if existing:
            raise ValueError(f"DN with number {dn_data.dn_number} already exists")

        # Calculate totals
        subtotal = sum(line.line_total for line in dn_data.lines)
        tax_amount = sum(line.line_total * Decimal("0.10") for line in dn_data.lines)  # Assume 10% tax
        total_amount = subtotal + tax_amount

        # Create DN data
        dn_dict = dn_data.model_dump(exclude={"lines"})
        dn_dict["subtotal"] = subtotal
        dn_dict["tax_amount"] = tax_amount
        dn_dict["total_amount"] = total_amount
        dn_dict["receipt_date"] = datetime.utcnow()
        if received_by:
            dn_dict["received_by"] = received_by

        # Create DN with lines
        dn = DeliveryNote(**dn_dict)
        self.db.add(dn)
        self.db.flush()

        # Create lines
        for line_data in dn_data.lines:
            line_dict = line_data.model_dump()
            line = DeliveryNoteLine(delivery_note_id=dn.id, **line_dict)
            self.db.add(line)

        self.db.commit()
        self.db.refresh(dn)

        # Audit log
        self.audit_service.log_create(dn, received_by)

        return dn

    def update_dn(self, id: str, dn_data: DeliveryNoteUpdate) -> Optional[DeliveryNote]:
        """Update Delivery Note."""
        dn = self.get_by_id(id)
        if not dn:
            return None

        update_dict = dn_data.model_dump(exclude_unset=True)
        
        # Audit before update
        self.audit_service.log_update(dn, update_dict, dn.received_by)

        return self.update(id, update_dict)

    def link_to_po(self, dn_id: str, po_id: str, matched_by: Optional[str] = None) -> Optional[DeliveryNote]:
        """Link DN to a PO."""
        dn = self.get_by_id(dn_id)
        if dn:
            dn.po_id = po_id
            self.db.commit()
            self.db.refresh(dn)
            self.audit_service.log_update(
                dn, {"po_id": po_id, "matched_by": matched_by}, matched_by
            )
        return dn

    def update_match_status(self, dn_id: str, match_score: Decimal, match_status: str) -> Optional[DeliveryNote]:
        """Update DN match status."""
        dn = self.get_by_id(dn_id)
        if dn:
            dn.match_score = match_score
            dn.match_status = match_status
            self.db.commit()
            self.db.refresh(dn)
        return dn

    def mark_as_received(self, dn_id: str, received_by: str) -> Optional[DeliveryNote]:
        """Mark DN as received."""
        dn = self.get_by_id(dn_id)
        if dn:
            dn.status = "received"
            dn.received_by = received_by
            self.db.commit()
            self.db.refresh(dn)
            self.audit_service.log_update(
                dn, {"status": "received", "received_by": received_by}, received_by
            )
        return dn
