// src/app/models/balance.py
"""Balance model for tracking partial matches."""

from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BalanceType(str, Enum):
    """Balance type enumeration."""

    INVOICE_BALANCE = "invoice_balance"
    DELIVERY_BALANCE = "delivery_balance"
    PO_BALANCE = "po_balance"


class Balance(BaseModel):
    """Balance model for tracking partial matches and remaining amounts."""

    __tablename__ = "balances"

    # Reference to original document
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_id: Mapped[UUID] = mapped_column(nullable=False)
    document_line_id: Mapped[UUID | None] = mapped_column(nullable=True)

    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(
        SQLEnum(BalanceType),
        nullable=False,
    )

    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Quantity tracking
    original_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    matched_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=True,
    )
    remaining_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )

    # Status
    is_settled: Mapped[bool] = mapped_column(default=False, nullable=False)
    settled_date: Mapped[Date | None] = mapped_column(nullable=True)

    # Reference to matching document
    matched_document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matched_document_id: Mapped[UUID | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Balance {self.balance_type} - {self.remaining_amount}>"

    @property
    def match_percentage(self) -> Decimal:
        """Calculate match percentage."""
        if self.original_amount == 0:
            return Decimal("0.00")
        return (self.matched_amount / self.original_amount) * 100
