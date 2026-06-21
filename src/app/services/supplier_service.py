// src/app/services/supplier_service.py
"""
Supplier service.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.base_service import BaseService


class SupplierService(BaseService[Supplier]):
    """Service for supplier operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Supplier, session)

    async def get_by_code(self, code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        return await self.get_by("code", code)

    async def get_by_tax_id(self, tax_id: str) -> Optional[Supplier]:
        """Get supplier by tax ID."""
        return await self.get_by("tax_id", tax_id)

    async def search(
        self,
        query: str = None,
        is_active: bool = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Supplier]:
        """Search suppliers."""
        stmt = select(Supplier)
        if query:
            stmt = stmt.where(
                Supplier.name.ilike(f"%{query}%") | Supplier.code.ilike(f"%{query}%")
            )
        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_supplier(self, supplier_in: SupplierCreate) -> Supplier:
        """Create a new supplier."""
        return await self.create(supplier_in.model_dump())

    async def update_supplier(
        self, id: UUID, supplier_in: SupplierUpdate
    ) -> Optional[Supplier]:
        """Update a supplier."""
        update_data = supplier_in.model_dump(exclude_unset=True)
        return await self.update(id, update_data)

    async def get_supplier_stats(self, id: UUID) -> dict:
        """Get supplier statistics."""
        supplier = await self.get(id)
        if not supplier:
            return None
        
        # Count purchase orders
        po_count = await self.session.execute(
            select(func.count()).select_from(supplier.purchase_orders)
        )
        
        # Count invoices
        invoice_count = await self.session.execute(
            select(func.count()).select_from(supplier.invoices)
        )
        
        # Count delivery notes
        dn_count = await self.session.execute(
            select(func.count()).select_from(supplier.delivery_notes)
        )
        
        return {
            "purchase_orders_count": po_count.scalar() or 0,
            "invoices_count": invoice_count.scalar() or 0,
            "delivery_notes_count": dn_count.scalar() or 0,
        }

    async def deactivate_supplier(self, id: UUID) -> Optional[Supplier]:
        """Deactivate a supplier."""
        return await self.update(id, {"is_active": False})

    async def activate_supplier(self, id: UUID) -> Optional[Supplier]:
        """Activate a supplier."""
        return await self.update(id, {"is_active": True})
