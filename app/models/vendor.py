# app/models/vendor.py
"""Vendor model for supplier management."""
from sqlalchemy import Column, String, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Vendor(Base, UUIDMixin, TimestampMixin):
    """Vendor (Supplier) model."""

    __tablename__ = "vendors"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    tax_id = Column(String(50), nullable=True, index=True)
    bank_name = Column(String(255), nullable=True)
    bank_account = Column(String(100), nullable=True)
    payment_terms_days = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")
    delivery_notes = relationship("DeliveryNote", back_populates="vendor")

    def __repr__(self) -> str:
        return f"<Vendor(id={self.id}, code={self.code}, name={self.name})>"
