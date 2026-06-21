// src/app/services/delivery_note_service.py
"""
Delivery Note Service
Handles delivery note-related business logic.
"""
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from app.services.base import BaseService


class DeliveryNoteService(BaseService[DeliveryNote]):
    """Service for Delivery Note operations."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(DeliveryNote, session)
    
    async def get_with_lines(self, dn_id: UUID) -> Optional[DeliveryNote]:
        """Get DN with all lines."""
        session = await self._get_session()
        result = await session.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.id == dn_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get DN by number."""
        session = await self._get_session()
        result = await session.execute(
            select(DeliveryNote).where(DeliveryNote.dn_number == dn_number)
        )
        return result.scalar_one_or_none()
    
    async def get_unmatched_dns(self, supplier_id: Optional[UUID] = None) -> List[DeliveryNote]:
        """Get all unmatched DNs."""
        session = await self._get_session()
        query = select(DeliveryNote).options(selectinload(DeliveryNote.lines)).where(
            DeliveryNote.status == "received"
        )
        
        if supplier_id:
            query = query.where(DeliveryNote.supplier_id == supplier_id)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def create_delivery_note(self, data: dict) -> DeliveryNote:
        """Create new delivery note with lines."""
        session = await self._get_session()
        
        # Extract lines data
        lines_data = data.pop("lines", [])
        
        # Create DN
        dn = DeliveryNote(**data)
        session.add(dn)
        await session.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data["dn_id"] = dn.id
            line = DeliveryNoteLine(**line_data)
            session.add(line)
        
        await session.flush()
        await session.refresh(dn)
        
        return await self.get_with_lines(dn.id)
    
    async def update_status(self, dn_id: UUID, status: str) -> Optional[DeliveryNote]:
        """Update DN status."""
        return await self.update(dn_id, {"status": status})
    
    async def get_statistics(self) -> dict:
        """Get DN statistics."""
        session = await self._get_session()
        
        total = await session.execute(select(func.count(DeliveryNote.id)))
        received = await session.execute(
            select(func.count(DeliveryNote.id)).where(DeliveryNote.status == "received")
        )
        matched = await session.execute(
            select(func.count(DeliveryNote.id)).where(DeliveryNote.status == "matched")
        )
        verified = await session.execute(
            select(func.count(DeliveryNote.id)).where(DeliveryNote.status == "verified")
        )
        
        return {
            "total": total.scalar_one(),
            "received": received.scalar_one(),
            "matched": matched.scalar_one(),
            "verified": verified.scalar_one(),
        }
