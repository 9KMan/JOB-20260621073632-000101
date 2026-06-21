// src/services/supplier_service.py
"""Supplier service for business logic."""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from src.models.supplier import Supplier
from src.services.base import BaseService


class SupplierService(BaseService[Supplier]):
    """Service for supplier operations."""

    def __init__(self, db: Session):
        """Initialize supplier service."""
        super().__init__(Supplier, db)

    def get_with_counts(self, id: UUID) -> Optional[dict]:
        """Get supplier with related record counts."""
        supplier = self.get(id)
        if not supplier:
            return None

        # Get counts
        po_count = self.db.execute(
            select(func.count()).where(
                Supplier.purchase_orders.any(id=id)
            )
        ).scalar()

        invoice_count = self.db.execute(
            select(func.count()).where(
                Supplier.invoices.any(id=id)
            )
        ).scalar()

        dn_count = self.db.execute(
            select(func.count()).where(
                Supplier.delivery_notes.any(id=id)
            )
        ).scalar()

        return {
            **supplier.__dict__,
            "purchase_orders_count": po_count,
            "invoices_count": invoice_count,
            "delivery_notes_count": dn_count,
        }

    def get_by_code(self, code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        return self.get_by_field("code", code)

    def get_by_tax_id(self, tax_id: str) -> Optional[Supplier]:
        """Get supplier by tax ID."""
        return self.get_by_field("tax_id", tax_id)

    def get_active_suppliers(self) -> list[Supplier]:
        """Get all active suppliers."""
        stmt = select(Supplier).where(
            Supplier.is_active == True,
            Supplier.is_deleted == False,  # noqa: E712
        ).order_by(Supplier.name)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, data: dict) -> Supplier:
        """Create a new supplier."""
        supplier = Supplier(**data)
        self.db.add(supplier)
        self.db.flush()
        self.db.refresh(supplier)
        return supplier

    def update(self, id: UUID, data: dict) -> Optional[Supplier]:
        """Update a supplier."""
        supplier = self.get(id)
        if supplier:
            for field, value in data.items():
                if hasattr(supplier, field) and value is not None:
                    setattr(supplier, field, value)
            self.db.flush()
            self.db.refresh(supplier)
        return supplier

    def deactivate(self, id: UUID) -> Optional[Supplier]:
        """Deactivate a supplier."""
        return self.update(id, {"is_active": False})

    def activate(self, id: UUID) -> Optional[Supplier]:
        """Activate a supplier."""
        return self.update(id, {"is_active": True})
