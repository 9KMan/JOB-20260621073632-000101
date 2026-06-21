# src/services/delivery_note_service.py
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.schemas.delivery_note import DeliveryNoteCreate, DeliveryNoteUpdate


class DeliveryNoteService:
    """Service for Delivery Note operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, dn_id: str) -> Optional[DeliveryNote]:
        """Get Delivery Note by ID with lines."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.id == dn_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, dn_number: str) -> Optional[DeliveryNote]:
        """Get Delivery Note by number."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.dn_number == dn_number)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[DeliveryNoteStatus] = None
    ) -> List[DeliveryNote]:
        """Get all Delivery Notes with pagination."""
        query = select(DeliveryNote).options(selectinload(DeliveryNote.lines))

        if status:
            query = query.where(DeliveryNote.status == status)

        result = await self.db.execute(
            query.offset(skip).limit(limit).order_by(DeliveryNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_supplier(
        self, supplier_id: str, skip: int = 0, limit: int = 100
    ) -> List[DeliveryNote]:
        """Get Delivery Notes by supplier."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .order_by(DeliveryNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_po_reference(
        self, po_reference: str, skip: int = 0, limit: int = 100
    ) -> List[DeliveryNote]:
        """Get Delivery Notes by PO reference."""
        result = await self.db.execute(
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.po_reference == po_reference)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unmatched(self, supplier_id: Optional[str] = None) -> List[DeliveryNote]:
        """Get unmatched delivery notes for matching."""
        query = (
            select(DeliveryNote)
            .options(selectinload(DeliveryNote.lines))
            .where(DeliveryNote.status.in_([DeliveryNoteStatus.RECEIVED, DeliveryNoteStatus.DRAFT]))
        )

        if supplier_id:
            query = query.where(DeliveryNote.supplier_id == supplier_id)

        result = await self.db.execute(query.order_by(DeliveryNote.delivery_date))
        return list(result.scalars().all())

    async def create(self, dn_data: DeliveryNoteCreate) -> DeliveryNote:
        """Create a new Delivery Note with lines."""
        # Calculate total amount (simplified - would normally come from pricing)
        total_amount = Decimal("0")

        dn = DeliveryNote(
            dn_number=dn_data.dn_number,
            supplier_id=dn_data.supplier_id,
            supplier_name=dn_data.supplier_name,
            supplier_code=dn_data.supplier_code,
            po_reference=dn_data.po_reference,
            delivery_date=dn_data.delivery_date,
            received_date=dn_data.received_date,
            currency=dn_data.currency,
            total_amount=total_amount,
            notes=dn_data.notes,
            metadata=dn_data.metadata,
            status=DeliveryNoteStatus.RECEIVED,
        )
        self.db.add(dn)
        await self.db.flush()

        # Create lines
        for line_data in dn_data.lines:
            dn_line = DeliveryNoteLine(
                delivery_note_id=dn.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                description=line_data.description,
                quantity_delivered=line_data.quantity_delivered,
                quantity_accepted=line_data.quantity_accepted,
                quantity_rejected=line_data.quantity_rejected,
                unit_of_measure=line_data.unit_of_measure,
                po_line_reference=line_data.po_line_reference,
                notes=line_data.notes,
            )
            self.db.add(dn_line)

        await self.db.flush()
        await self.db.refresh(dn)
        return dn

    async def update(self, dn_id: str, dn_data: DeliveryNoteUpdate) -> Optional[DeliveryNote]:
        """Update an existing Delivery Note."""
        dn = await self.get_by_id(dn_id)
        if not dn:
            return None

        update_data = dn_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dn, field, value)

        await self.db.flush()
        await self.db.refresh(dn)
        return dn

    async def update_status(self, dn_id: str, status: DeliveryNoteStatus) -> Optional[DeliveryNote]:
        """Update Delivery Note status."""
        dn = await self.get_by_id(dn_id)
        if not dn:
            return None
        dn.status = status
        await self.db.flush()
        await self.db.refresh(dn)
        return dn

    async def delete(self, dn_id: str) -> bool:
        """Delete a Delivery Note."""
        dn = await self.get_by_id(dn_id)
        if not dn:
            return False
        await self.db.delete(dn)
        await self.db.flush()
        return True
