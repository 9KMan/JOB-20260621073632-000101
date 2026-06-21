// src/app/models/user.py
"""User model for authentication."""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel


class User(BaseModel):
    """User model for system authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="PurchaseOrder.created_by",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Invoice.created_by",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="DeliveryNote.created_by",
    )
    match_confirmations: Mapped[list["MatchConfirmation"]] = relationship(
        back_populates="confirmed_by_user",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
