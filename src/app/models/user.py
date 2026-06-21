# src/app/models/user.py
"""User model for authentication."""
import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote
    from src.app.models.matching import MatchResult


class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Relationships
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="created_by_user",
        foreign_keys="PurchaseOrder.created_by",
    )
    
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="created_by_user",
        foreign_keys="Invoice.created_by",
    )
    
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="created_by_user",
        foreign_keys="DeliveryNote.created_by",
    )
    
    match_results: Mapped[List["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="reviewed_by_user",
        foreign_keys="MatchResult.reviewed_by",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
