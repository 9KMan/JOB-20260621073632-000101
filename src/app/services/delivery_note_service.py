// src/app/services/delivery_note_service.py
"""Delivery Note service."""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.app.schemas.delivery_note import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
    DeliveryNoteResponse,
    DeliveryNoteSummary,
)


class DeliveryNoteService:
    """Service for Delivery Note operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_delivery_note(self, dn_data: DeliveryNoteCreate) -> DeliveryNote:
        """Create a new delivery note with lines."""
        dn = DeliveryNote(
            dn_number=dn_data.dn_number,
            supplier_id=uuid.UUID(dn_data.supplier_id),
            supplier_name=dn_data.supplier_name,
            supplier_code=dn_data.supplier_code,
            dn_date=dn_data.dn_date,
            received_date=dn_data.received_date,
            po_reference=dn_data.po_reference,
            currency=dn_data.currency,
            status=dn_data.status or DeliveryNoteStatus.DRAFT.value,
            notes=dn_data.notes,
        )
        
        self.db.add(dn)
        await self.db.flush()
        
        for line_data in dn_data.lines:
            line = DeliveryNoteLine(
                delivery_note_id=dn.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                product_name=line_data.product_name,
                description=line_data.description,
                quantity_ordered=line_data.quantity_ordered,
                quantity_delivered=line_data.quantity_delivered,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                notes=line_data.notes,
            )
            if line_data.unit_price:
                line.line_amount = line_data.quantity_delivered * line_data.unit_price
            else:
                line.line_amount = Decimal("0.00")
            self.db.add(line)
        
        await self.db.flush()
        await self._recalculate_totals(dn.id)
        await self.db.refresh(dn)
        
        return dn
    
    async def get_delivery_note(self, dn_id: str) -> Optional[DeliveryNote]:
        """Get a delivery note by ID."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.id == uuid.UUID(dn_id))
        )
        return result.scalar_one_or_none()
    
    async def get_delivery_note_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get a delivery note by DN number."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.dn_number == dn_number)
        )
        return result.scalar_one_or_none()
    
    async def list_delivery_notes(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_code: Optional[str] = None,
        status: Optional[str] = None,
        po_reference: Optional[str] = None,
        is_archived: bool = False,
    ) -> tuple[list[DeliveryNote], int]:
        """List delivery notes with pagination and filters."""
        query = select(DeliveryNote).options(selectinload(DeliveryNote.lines))
        
        if supplier_code:
            query = query.where(DeliveryNote.supplier_code == supplier_code)
        if status:
            query = query.where(DeliveryNote.status == status)
        if po_reference:
            query = query.where(DeliveryNote.po_reference == po_reference)
        if is_archived is not None:
            query = query.where(DeliveryNote.is_archived == is_archived)
        
        count_query = select(func.count(DeliveryNote.id))
        if supplier_code:
            count_query = count_query.where(DeliveryNote.supplier_code == supplier_code)
        if status:
            count_query = count_query.where(DeliveryNote.status == status)
        if po_reference:
            count_query = count_query.where(DeliveryNote.po_reference == po_reference)
        if is_archived is not None:
            count_query = count_query.where(DeliveryNote.is_archived == is_archived)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(DeliveryNote.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        delivery_notes = result.scalars().all()
        
        return list(delivery_notes), total
    
    async def update_delivery_note(
        self,
        dn_id: str,
        dn_data: DeliveryNoteUpdate,
    ) -> Optional[DeliveryNote]:
        """Update a delivery note."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        
        update_data = dn_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dn, field, value)
        
        await self.db.flush()
        await self.db.refresh(dn)
        return dn
    
    async def delete_delivery_note(self, dn_id: str) -> bool:
        """Delete a delivery note."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return False
        
        await self.db.delete(dn)
        await self.db.flush()
        return True
    
    async def archive_delivery_note(self, dn_id: str) -> Optional[DeliveryNote]:
        """Archive a delivery note."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        
        dn.is_archived = True
        await self.db.flush()
        await self.db.refresh(dn)
        return dn
    
    async def update_status(self, dn_id: str, status: str) -> Optional[DeliveryNote]:
        """Update delivery note status."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        
        dn.status = status
        await self.db.flush()
        await self.db.refresh(dn)
        return dn
    
    async def link_to_po(self, dn_id: str, po_id: str) -> Optional[DeliveryNote]:
        """Link delivery note to purchase order."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        
        dn.po_id = uuid.UUID(po_id)
        await self.db.flush()
        await self.db.refresh(dn)
        return dn
    
    async def get_open_delivery_notes(
        self,
        supplier_code: Optional[str] = None,
    ) -> list[DeliveryNote]:
        """Get all open (unmatched) delivery notes."""
        query = select(DeliveryNote).options(selectinload(DeliveryNote.lines)).where(
            DeliveryNote.status == DeliveryNoteStatus.RECEIVED.value,
            DeliveryNote.is_archived == False,
        )
        
        if supplier_code:
            query = query.where(DeliveryNote.supplier_code == supplier_code)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_delivery_note_summary(self, dn_id: str) -> Optional[DeliveryNoteSummary]:
        """Get delivery note summary for matching."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        
        return DeliveryNoteSummary(
            id=str(dn.id),
            dn_number=dn.dn_number,
            supplier_code=dn.supplier_code,
            total_amount=dn.total_amount,
            currency=dn.currency,
            status=dn.status,
            open_amount=dn.total_amount,
            line_count=len(dn.lines),
        )
    
    async def _recalculate_totals(self, dn_id: uuid.UUID) -> None:
        """Recalculate delivery note totals from lines."""
        result = await self.db.execute(
            select(func.sum(DeliveryNoteLine.line_amount).label("total"))
            .where(DeliveryNoteLine.delivery_note_id == dn_id)
        )
        total = result.scalar() or Decimal("0.00")
        
        dn_result = await self.db.execute(
            select(DeliveryNote).where(DeliveryNote.id == dn_id)
        )
        dn = dn_result.scalar_one()
        dn.total_amount = total
        await self.db.flush()
