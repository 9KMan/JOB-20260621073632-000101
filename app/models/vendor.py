// app/models/vendor.py
"""Vendor model for supplier management."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice


class Vendor(Base):
    """Vendor (Supplier) model for AP automation."""
    
    __tablename__ = "vendors"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Vendor identification
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    
    short_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Tax information
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Payment terms
    payment_terms_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    payment_terms_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Credit limits
    credit_limit: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    
    current_balance: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="vendor",
    )
    
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="vendor",
    )
    
    def __repr__(self) -> str:
        return f"<Vendor {self.code}: {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert vendor to dictionary."""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "short_name": self.short_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "tax_id": self.tax_id,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "payment_terms_code": self.payment_terms_code,
            "payment_terms_days": self.payment_terms_days,
            "credit_limit": self.credit_limit,
            "current_balance": self.current_balance,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
