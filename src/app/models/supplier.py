// src/app/models/supplier.py
"""
Supplier Model
Vendor/supplier management for the AP system.
"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Supplier(BaseModel):
    """Supplier/vendor model."""
    
    __tablename__ = "suppliers"
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )
    tax_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    bank_account: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_terms_days: Mapped[int] = mapped_column(
        default=30,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<Supplier {self.code}: {self.name}>"
