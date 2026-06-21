// src/services/supplier_service.py
"""Supplier service."""
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.supplier import Supplier
from src.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierService:
    """Service for supplier operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """Create a new supplier."""
        supplier = Supplier(
            code=supplier_data.code,
            name=supplier_data.name,
            email=supplier_data.email,
            phone=supplier_data.phone,
            address=supplier_data.address,
            tax_id=supplier_data.tax_id,
            is_active=supplier_data.is_active,
        )
        
        self.db.add(supplier)
        await self.db.commit()
        await self.db.refresh(supplier)
        
        return supplier

    async def get_supplier_by_id(self, supplier_id: uuid.UUID) -> Optional[Supplier]:
        """Get a supplier by ID."""
        result = await self.db.execute(
            select(Supplier).where(
                Supplier.id == supplier_id,
                Supplier.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        """Get a supplier by code."""
        result = await self.db.execute(
            select(Supplier).where(
                Supplier.code == code,
                Supplier.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def update_supplier(
        self,
        supplier_id: uuid.UUID,
        supplier_data: SupplierUpdate
    ) -> Optional[Supplier]:
        """Update an existing supplier."""
        supplier = await self.get_supplier_by_id(supplier_id)
        if not supplier:
            return None
        
        update_data = supplier_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(supplier, field, value)
        
        await self.db.commit()
        await self.db.refresh(supplier)
        
        return supplier

    async def delete_supplier(self, supplier_id: uuid.UUID) -> bool:
        """Soft delete a supplier."""
        supplier = await self.get_supplier_by_id(supplier_id)
        if not supplier:
            return False
        
        supplier.soft_delete()
        await self.db.commit()
        
        return True

    async def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[list[Supplier], int]:
        """List suppliers with pagination and filtering."""
        query = select(Supplier).where(Supplier.is_deleted == False)
        
        if is_active is not None:
            query = query.where(Supplier.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Supplier.code.ilike(search_term)) |
                (Supplier.name.ilike(search_term))
            )
        
        # Get total count
        count_query = select(func.count(Supplier.id)).where(Supplier.is_deleted == False)
        if is_active is not None:
            count_query = count_query.where(Supplier.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (Supplier.code.ilike(search_term)) |
                (Supplier.name.ilike(search_term))
            )
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Supplier.name)
        result = await self.db.execute(query)
        suppliers = result.scalars().all()
        
        return list(suppliers), total
