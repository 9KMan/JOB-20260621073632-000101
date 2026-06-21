// src/services/delivery_note.py
"""Delivery note service."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate


class DeliveryNoteService:
    """Delivery note business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _calculate_line_total(self, line: dict) -> Decimal:
        """Calculate line total."""
        quantity = Decimal(str(line.quantity))
        return quantity
    
    def _calculate_total(self, lines: list[dict]) -> Decimal:
        """Calculate total amount."""
        return Decimal("0.00")
    
    async def create_delivery_note(self, dn_data: DeliveryNoteCreate) -> DeliveryNote:
        """Create a new delivery note."""
        lines_data = [line.model_dump() for line in dn_data.lines]
        total_amount = Decimal("0.00")
        
        dn = DeliveryNote(
            dn_number=dn_data.dn_number,
            supplier_id=dn_data.supplier_id,
            supplier_name=dn_data.supplier_name,
            supplier_reference=dn_data.supplier_reference,
            po_reference=dn_data.po_reference,
            delivery_date=dn_data.delivery_date,
            received_date=dn_data.received_date,
            currency=dn_data.currency,
            total_amount=total_amount,
            notes=dn_data.notes,
            status=DeliveryNoteStatus.DRAFT,
        )
        self.db.add(dn)
        await self.db.flush()
        
        for idx, line_data in enumerate(lines_data):
            line_total = self._calculate_line_total(line_data)
            total_amount += line_total
            line = DeliveryNoteLine(
                delivery_note_id=dn.id,
                line_number=line_data.get("line_number", idx + 1),
                sku=line_data.get("sku"),
                description=line_data["description"],
                quantity=Decimal(str(line_data["quantity"])),
                unit_of_measure=line_data.get("unit_of_measure", "EA"),
                line_total=line_total,
            )
            self.db.add(line)
        
        dn.total_amount = total_amount
        await self.db.commit()
        await self.db.refresh(dn)
        return dn
    
    async def get_delivery_note(self, dn_id: UUID) -> Optional[DeliveryNote]:
        """Get delivery note by ID."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.id == dn_id)
        )
        return result.scalar_one_or_none()
    
    async def get_delivery_note_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get delivery note by number."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.dn_number == dn_number)
        )
        return result.scalar_one_or_none()
    
    async def get_delivery_notes(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_id: Optional[str] = None,
        status: Optional[DeliveryNoteStatus] = None,
        po_reference: Optional[str] = None,
    ) -> tuple[list[DeliveryNote], int]:
        """Get delivery notes with optional filters."""
        query = select(DeliveryNote).options(selectinload(DeliveryNote.lines))
        count_query = select(func.count(DeliveryNote.id))
        
        if supplier_id:
            query = query.where(DeliveryNote.supplier_id == supplier_id)
            count_query = count_query.where(DeliveryNote.supplier_id == supplier_id)
        
        if status:
            query = query.where(DeliveryNote.status == status)
            count_query = count_query.where(DeliveryNote.status == status)
        
        if po_reference:
            query = query.where(DeliveryNote.po_reference == po_reference)
            count_query = count_query.where(DeliveryNote.po_reference == po_reference)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(skip).limit(limit).order_by(DeliveryNote.created_at.desc())
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return items, total
    
    async def update_delivery_note(
        self,
        dn_id: UUID,
        dn_data: DeliveryNoteUpdate,
    ) -> Optional[DeliveryNote]:
        """Update a delivery note."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        
        update_data = dn_data.model_dump(exclude_unset=True)
        
        if "lines" in update_data:
            lines_data = update_data.pop("lines")
            for line in dn.lines:
                await self.db.delete(line)
            await self.db.flush()
            
            total_amount = Decimal("0.00")
            for idx, line_data in enumerate(lines_data):
                line_total = self._calculate_line_total(line_data)
                total_amount += line_total
                line = DeliveryNoteLine(
                    delivery_note_id=dn.id,
                    line_number=line_data.get("line_number", idx + 1),
                    sku=line_data.get("sku"),
                    description=line_data["description"],
                    quantity=Decimal(str(line_data["quantity"])),
                    unit_of_measure=line_data.get("unit_of_measure", "EA"),
                    line_total=line_total,
                )
                self.db.add(line)
            update_data["total_amount"] = total_amount
        
        for field, value in update_data.items():
            setattr(dn, field, value)
        
        await self.db.commit()
        await self.db.refresh(dn)
        return dn
    
    async def update_dn_status(
        self,
        dn_id: UUID,
        status: DeliveryNoteStatus,
    ) -> Optional[DeliveryNote]:
        """Update delivery note status."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return None
        dn.status = status
        await self.db.commit()
        await self.db.refresh(dn)
        return dn
    
    async def delete_delivery_note(self, dn_id: UUID) -> bool:
        """Delete a delivery note."""
        dn = await self.get_delivery_note(dn_id)
        if not dn:
            return False
        await self.db.delete(dn)
        await self.db.commit()
        return True
