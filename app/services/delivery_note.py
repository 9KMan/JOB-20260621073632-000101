// app/services/delivery_note.py
"""Delivery Note service."""
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from app.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate


class DeliveryNoteService:
    """Service for delivery note operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dn_by_id(self, dn_id: uuid.UUID) -> Optional[DeliveryNote]:
        """Get a delivery note by ID with lines."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(
                and_(DeliveryNote.id == dn_id, DeliveryNote.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_dn_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get a delivery note by DN number."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(
                and_(DeliveryNote.dn_number == dn_number, DeliveryNote.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_delivery_notes(
        self,
        skip: int = 0,
        limit: int = 100,
        vendor_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        po_reference: Optional[str] = None,
    ) -> List[DeliveryNote]:
        """Get a list of delivery notes."""
        query = select(DeliveryNote).options(
            selectinload(DeliveryNote.lines)
        ).where(DeliveryNote.is_deleted == False)
        
        if vendor_id:
            query = query.where(DeliveryNote.vendor_id == vendor_id)
        if status:
            query = query.where(DeliveryNote.status == status)
        if po_reference:
            query = query.where(DeliveryNote.po_reference == po_reference)
        
        query = query.offset(skip).limit(limit).order_by(DeliveryNote.delivery_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_unmatched_delivery_notes(
        self,
        vendor_id: Optional[uuid.UUID] = None,
    ) -> List[DeliveryNote]:
        """Get delivery notes that haven't been matched yet."""
        query = select(DeliveryNote).options(
            selectinload(DeliveryNote.lines)
        ).where(
            and_(
                DeliveryNote.is_deleted == False,
                DeliveryNote.status == "RECEIVED",
            )
        )
        if vendor_id:
            query = query.where(DeliveryNote.vendor_id == vendor_id)
        query = query.order_by(DeliveryNote.delivery_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_delivery_note(self, dn_data: DeliveryNoteCreate) -> DeliveryNote:
        """Create a new delivery note with lines."""
        dn_dict = dn_data.model_dump(exclude={"lines"})
        
        # Calculate totals from lines
        lines_data = dn_dict.pop("lines", [])
        
        # Calculate line totals if not provided
        for line in lines_data:
            if "line_total" not in line or line["line_total"] is None:
                quantity = Decimal(str(line["quantity_delivered"]))
                unit_price = Decimal(str(line["unit_price"]))
                line["line_total"] = quantity * unit_price
        
        # Calculate DN totals (no tax for delivery notes typically)
        subtotal = sum(Decimal(str(line["line_total"])) for line in lines_data)
        tax_amount = Decimal("0.00")
        
        dn_dict["subtotal"] = subtotal
        dn_dict["tax_amount"] = tax_amount
        dn_dict["total_amount"] = subtotal + tax_amount
        
        # Create delivery note
        dn = DeliveryNote(**dn_dict)
        self.db.add(dn)
        await self.db.flush()
        
        # Create lines
        for line_data in lines_data:
            line_data["delivery_note_id"] = dn.id
            line = DeliveryNoteLine(**line_data)
            self.db.add(line)
        
        await self.db.flush()
        await self.db.refresh(dn)
        return dn
    
    async def update_delivery_note(
        self,
        dn_id: uuid.UUID,
        dn_data: DeliveryNoteUpdate,
    ) -> Optional[DeliveryNote]:
        """Update an existing delivery note."""
        dn = await self.get_dn_by_id(dn_id)
        if not dn:
            return None
        
        update_data = dn_data.model_dump(exclude_unset=True, exclude={"lines"})
        
        # Handle line updates if provided
        if "lines" in update_data and update_data["lines"] is not None:
            # Delete existing lines and create new ones
            for existing_line in dn.lines:
                await self.db.delete(existing_line)
            
            lines_data = update_data.pop("lines")
            for line_data in lines_data:
                if "line_total" not in line_data or line_data["line_total"] is None:
                    quantity = Decimal(str(line_data["quantity_delivered"]))
                    unit_price = Decimal(str(line_data["unit_price"]))
                    line_data["line_total"] = quantity * unit_price
                line_data["delivery_note_id"] = dn.id
                line = DeliveryNoteLine(**line_data)
                self.db.add(line)
        
        # Update DN fields
        for field, value in update_data.items():
            setattr(dn, field, value)
        
        # Recalculate totals
        await self.db.flush()
        await self.db.refresh(dn)
        await self._recalculate_totals(dn)
        
        return dn
    
    async def _recalculate_totals(self, dn: DeliveryNote) -> None:
        """Recalculate delivery note totals from lines."""
        lines = await self.db.execute(
            select(DeliveryNoteLine)
            .where(DeliveryNoteLine.delivery_note_id == dn.id)
        )
        lines = list(lines.scalars().all())
        
        subtotal = sum(line.line_total for line in lines)
        tax_amount = Decimal("0.00")
        
        dn.subtotal = subtotal
        dn.tax_amount = tax_amount
        dn.total_amount = subtotal + tax_amount
        await self.db.flush()
    
    async def update_dn_status(
        self,
        dn_id: uuid.UUID,
        status: str,
    ) -> Optional[DeliveryNote]:
        """Update delivery note status."""
        dn = await self.get_dn_by_id(dn_id)
        if not dn:
            return None
        dn.status = status
        await self.db.flush()
        await self.db.refresh(dn)
        return dn
    
    async def delete_dn(self, dn_id: uuid.UUID) -> bool:
        """Soft delete a delivery note."""
        dn = await self.get_dn_by_id(dn_id)
        if not dn:
            return False
        
        dn.is_deleted = True
        dn.deleted_at = dn.updated_at
        await self.db.flush()
        return True
