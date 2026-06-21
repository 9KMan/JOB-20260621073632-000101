// src/models/user.py
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="created_by_user")
    invoices = relationship("Invoice", back_populates="created_by_user")
    delivery_notes = relationship("DeliveryNote", back_populates="created_by_user")
    matches = relationship("Match", back_populates="reviewed_by_user")
    
    def __repr__(self):
        return f"<User {self.username}>"
