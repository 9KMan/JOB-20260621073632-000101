// src/models/user.py
"""
User model for authentication
"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from src.models.base import UUIDModel, TimestampModel, SoftDeleteModel


class User(UUIDModel, TimestampModel, SoftDeleteModel):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    created_purchase_orders = relationship(
        "PurchaseOrder",
        back_populates="created_by_user",
        foreign_keys="PurchaseOrder.created_by"
    )
    created_invoices = relationship(
        "Invoice",
        back_populates="created_by_user",
        foreign_keys="Invoice.created_by"
    )
    created_delivery_notes = relationship(
        "DeliveryNote",
        back_populates="created_by_user",
        foreign_keys="DeliveryNote.created_by"
    )
    confirmed_matches = relationship(
        "MatchRecord",
        back_populates="confirmed_by_user",
        foreign_keys="MatchRecord.confirmed_by"
    )
    
    def __repr__(self):
        return f"<User {self.email}>"
