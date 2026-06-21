// src/app/services/delivery_note_service.py
"""
Delivery Note service.
"""
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from app.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate
from app.services.base_service import BaseService


class DeliveryNoteService(BaseService[DeliveryNote]):
    """Service for Delivery Note operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(DeliveryNote, session)

    async def get_by_dn_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get delivery note by DN number."""
        return await self.get_by(
            "dn_number", dn_number, load_relations=["lines", "supplier"]
        )

    async def get_with_relations(self, id: UUID) -> Optional[DeliveryNote]:
        """Get delivery note with all relations loaded."""
        result = await self.session.execute(
            select(DeliveryNote)
            .options(
                selectinload(DeliveryNote.lines),
                selectinload(DeliveryNote.supplier),
            )
            .where(DeliveryNote.id == id)
        )
        return result.scalar_one_or_none()

    async def search_delivery_notes(
        self,
        query: str = None,
        supplier_id: UUID = None,
        status: str = None,
        date_from: date = None,
        date_to: date = None,
        po_reference: str = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DeliveryNote]:
        """Search delivery notes."""
        stmt = select(DeliveryNote).options(selectinload(DeliveryNote.lines))
        
        if query:
            stmt = stmt.where(DeliveryNote.dn_number.ilike(f"%{query}%"))
        if supplier_id:
            stmt = stmt.where(DeliveryNote.supplier_id == supplier_id)
        if status:
            stmt = stmt.where(DeliveryNote.status == status)
        if date_from:
            stmt = stmt.where(DeliveryNote.delivery_date >= date_from)
        if date_to:
            stmt = stmt.where(DeliveryNote.delivery_date <= date_to)
        if po_reference:
            stmt = stmt.where(DeliveryNote.po_reference == po_reference)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_delivery_note(
        self, dn_in: DeliveryNoteCreate
    ) -> DeliveryNote:
        """Create a new delivery note with lines."""
        dn_data = dn_in.model_dump(exclude={"lines"})
        
        # Create delivery note
        dn = DeliveryNote(**dn_data)
        self.session.add(dn)
        await self.session.flush()
        
        # Create lines
        lines_data = dn_data.pop("lines")
        for line_data in lines_data:
            line = DeliveryNoteLine(delivery_note_id=dn.id, **line_data)
            self.session.add(line)
        
        await self.session.flush()
        await self.session.refresh(dn)
        
        return await self.get_with_relations(dn.id)

    async def update_delivery_note(
        self, id: UUID, dn_in: DeliveryNoteUpdate
    ) -> Optional[DeliveryNote]:
        """Update a delivery note."""
        update_data = dn_in.model_dump(exclude_unset=True)
        return await self.update(id, update_data)

    async def update_dn_status(self, id: UUID, status: str) -> Optional[DeliveryNote]:
        """Update delivery note status."""
        return await self.update(id, {"status": status})

    async def mark_as_matched(self, id: UUID) -> Optional[DeliveryNote]:
        """Mark delivery note as matched."""
        return await self.update(id, {"status": "matched"})

    async def mark_as_completed(self, id: UUID) -> Optional[DeliveryNote]:
        """Mark delivery note as completed."""
        return await self.update(id, {"status": "completed"})

    async def get_unmatched_delivery_notes(
        self,
        supplier_id: UUID = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DeliveryNote]:
        """Get delivery notes that haven't been matched."""
        stmt = (
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.status == "pending")
        )
        if supplier_id:
            stmt = stmt.where(DeliveryNote.supplier_id == supplier_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_quantity(self, id: UUID) -> Decimal:
        """Get total quantity delivered for a DN."""
        dn = await self.get_with_relations(id)
        if not dn:
            return Decimal("0.000")
        return sum(line.net_quantity for line in dn.lines)

    async def get_pending_delivery_notes_for_review(
        self, skip: int = 0, limit: int = 100
    ) -> List[DeliveryNote]:
        """Get all pending delivery notes that need review."""
        stmt = (
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines), selectinload(DeliveryNote.supplier))
            .where(DeliveryNote.status == "pending")
            .order_by(DeliveryNote.delivery_date.desc())
        )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
