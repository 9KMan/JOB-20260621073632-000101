// app/services/vendor.py
"""Vendor service."""
import uuid
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


class VendorService:
    """Service for vendor operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_vendor_by_id(self, vendor_id: uuid.UUID) -> Optional[Vendor]:
        """Get a vendor by ID."""
        result = await self.db.execute(
            select(Vendor).where(
                and_(Vendor.id == vendor_id, Vendor.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_vendor_by_code(self, code: str) -> Optional[Vendor]:
        """Get a vendor by code."""
        result = await self.db.execute(
            select(Vendor).where(
                and_(Vendor.code == code, Vendor.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_vendors(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Vendor]:
        """Get a list of vendors."""
        query = select(Vendor).where(Vendor.is_deleted == False)
        if active_only:
            query = query.where(Vendor.is_active == True)
        query = query.offset(skip).limit(limit).order_by(Vendor.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        """Create a new vendor."""
        vendor = Vendor(**vendor_data.model_dump())
        self.db.add(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor
    
    async def update_vendor(
        self,
        vendor_id: uuid.UUID,
        vendor_data: VendorUpdate,
    ) -> Optional[Vendor]:
        """Update an existing vendor."""
        vendor = await self.get_vendor_by_id(vendor_id)
        if not vendor:
            return None
        
        update_data = vendor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)
        
        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor
    
    async def delete_vendor(self, vendor_id: uuid.UUID) -> bool:
        """Soft delete a vendor."""
        vendor = await self.get_vendor_by_id(vendor_id)
        if not vendor:
            return False
        
        vendor.is_deleted = True
        vendor.deleted_at = vendor.updated_at
        await self.db.flush()
        return True
