// src/services/supplier_service.py
"""Supplier service."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.supplier import Supplier
from src.schemas.supplier import SupplierCreate, SupplierUpdate
from src.services.base_service import BaseService


class SupplierService(BaseService[Supplier, SupplierCreate, SupplierUpdate]):
    """Service for supplier operations."""
    
    def __init__(self, db: Session):
        super().__init__(Supplier, db)
    
    def get_by_code(self, code: str) -> Optional[Supplier]:
        """Get a supplier by code."""
        return self.get_by(code=code)
    
    def get_active_suppliers(self) -> List[Supplier]:
        """Get all active suppliers."""
        return self.get_all(is_active=True)
    
    def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """Create a new supplier."""
        return self.create(supplier_data)
    
    def update_supplier(
        self,
        supplier_id: UUID,
        update_data: SupplierUpdate
    ) -> Optional[Supplier]:
        """Update a supplier."""
        return self.update(supplier_id, update_data)
    
    def deactivate_supplier(self, supplier_id: UUID) -> bool:
        """Soft delete/deactivate a supplier."""
        supplier = self.get(supplier_id)
        if supplier:
            supplier.is_active = False
            self.db.commit()
            return True
        return False
