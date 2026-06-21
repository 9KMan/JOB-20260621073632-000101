// src/services/delivery_note_service.py
"""Delivery Note service for business logic."""
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.services.base import BaseService


class DeliveryNoteService(BaseService[DeliveryNote]):
    """Service for Delivery Note operations."""

    def __init__(self, db: Session):
        """Initialize DN service."""
        super().__init__(DeliveryNote, db)

    def get_with_lines(self, id: UUID) -> Optional[DeliveryNote]:
        """Get DN with lines eagerly loaded."""
        stmt = (
            select(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .options(joinedload(DeliveryNote.supplier))
            .where(
                DeliveryNote.id == id,
                DeliveryNote.is_deleted == False,  # noqa: E712
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get DN by DN number."""
        return self.get_by_field("dn_number", dn_number)

    def get_by_supplier_and_number(
        self, supplier_id: UUID, dn_number: str
    ) -> Optional[DeliveryNote]:
        """Get DN by supplier and DN number."""
        stmt = select(DeliveryNote).where(
            DeliveryNote.supplier_id == supplier_id,
            DeliveryNote.dn_number == dn_number,
            DeliveryNote.is_deleted == False,  # noqa: E712
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_pending_dns(self) -> List[DeliveryNote]:
        """Get all pending DNs (for matching)."""
        stmt = (
            select(DeliveryNote)
            .options(joinedload(DeliveryNote.lines))
            .options(joinedload(DeliveryNote.supplier))
            .where(
                DeliveryNote.status == DeliveryNoteStatus.ISSUED,
                DeliveryNote.is_deleted == False,  # noqa: E712
            )
            .order_by(DeliveryNote.issue_date)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, data: dict) -> DeliveryNote:
        """Create a new DN with lines."""
        lines_data = data.pop("lines", [])

        dn = DeliveryNote(**data)
        self.db.add(dn)
        self.db.flush()

        # Create lines
        for line_data in lines_data:
            line_data["dn_id"] = dn.id
            line = DeliveryNoteLine(**line_data)
            self.db.add(line)

        self.db.flush()
        self.db.refresh(dn)
        return dn

    def update(self, id: UUID, data: dict) -> Optional[DeliveryNote]:
        """Update a DN."""
        dn = self.get(id)
        if dn:
            lines_data = data.pop("lines", None)

            for field, value in data.items():
                if hasattr(dn, field) and value is not None:
                    setattr(dn, field, value)

            if lines_data is not None:
                # Update lines
                for line_data in lines_data:
                    line_id = line_data.pop("id", None)
                    if line_id:
                        line = self.db.get(DeliveryNoteLine, line_id)
                        if line:
                            for field, value in line_data.items():
                                if hasattr(line, field) and value is not None:
                                    setattr(line, field, value)
                    else:
                        line_data["dn_id"] = dn.id
                        line = DeliveryNoteLine(**line_data)
                        self.db.add(line)

            self.db.flush()
            self.db.refresh(dn)
        return dn

    def update_status(self, id: UUID, status: DeliveryNoteStatus) -> Optional[DeliveryNote]:
        """Update DN status."""
        return self.update(
            id, {"status": status.value if isinstance(status, DeliveryNoteStatus) else status}
        )

    def get_multi_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[DeliveryNote], int]:
        """Get DNs with pagination and filters."""
        stmt = (
            select(DeliveryNote)
            .options(joinedload(DeliveryNote.supplier))
            .options(joinedload(DeliveryNote.lines))
            .where(DeliveryNote.is_deleted == False)  # noqa: E712
        )

        if supplier_id:
            stmt = stmt.where(DeliveryNote.supplier_id == supplier_id)

        if status:
            stmt = stmt.where(DeliveryNote.status == status)

        if search:
            stmt = stmt.where(DeliveryNote.dn_number.ilike(f"%{search}%"))

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar()

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size).order_by(DeliveryNote.created_at.desc())

        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total
