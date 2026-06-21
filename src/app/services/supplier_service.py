// src/app/services/supplier_service.py
"""
Supplier Service
Handles supplier-related business logic.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.services.base import BaseService


class SupplierService(BaseService[Supplier]):
    """Service for supplier operations."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(Supplier, session)
    
    async def get_by_code(self, code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        session = await self._get_session()
        result = await session.execute(
            select(Supplier).where(Supplier.code == code.upper())
        )
        return result.scalar_one_or_none()
    
    async def get_active_suppliers(self) -> List[Supplier]:
        """Get all active suppliers."""
        return await self.get_all(filters={"is_active": True})
    
    async def create_supplier(self, data: dict) -> Supplier:
        """Create new supplier."""
        if "code" in data:
            data["code"] = data["code"].upper()
        return await self.create(data)
    
    async def deactivate(self, supplier_id: UUID) -> Optional[Supplier]:
        """Deactivate a supplier."""
        return await self.update(supplier_id, {"is_active": False})
    
    async def activate(self, supplier_id: UUID) -> Optional[Supplier]:
        """Activate a supplier."""
        return await self.update(supplier_id, {"is_active": True})
