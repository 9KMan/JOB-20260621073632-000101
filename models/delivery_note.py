# models/delivery_note.py
"""Delivery Note and DeliveryNoteLine SQLAlchemy models.

Delivery notes record received goods and are used in 3-way matching.
They provide proof of delivery to match against purchase orders and invoices.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import DeliveryNoteStatus, LineStatus

if TYPE_CHECKING:
    from models.purchase_order import POLine, PurchaseOrder


class DeliveryNoteLine(Base):
    """Delivery note line item model.

    Represents a single line item on a delivery note.
    """

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        UniqueConstraint("dn_id", "line_number", name="uq_dn_line_number"),
        Index("ix_dn_lines_dn_id", "dn_id"),
        Index("ix_dn_lines_po_line_id", "po_line_id"),
        Index("ix_dn_lines_product_code", "product_code"),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        default=LineStatus.PENDING,
        nullable=False,
    )
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    dn: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    po_line: Mapped["POLine"] = relationship(
        "POLine",
        back_populates="delivery_note_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="dn_line",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.description}>"


class DeliveryNote(Base):
    """Delivery Note model.

    Represents a delivery note confirming goods received from a vendor.
    Used in 3-way matching with purchase orders and invoices.
    """

    __tablename__ = "delivery_notes"
    __table_args__ = (
        UniqueConstraint("dn_number", "vendor_id", name="uq_dn_vendor"),
        Index("ix_dns_dn_number", "dn_number"),
        Index("ix_dns_vendor_id", "vendor_id"),
        Index("ix_dns_vendor_code", "vendor_code"),
        Index("ix_dns_status", "status"),
        Index("ix_dns_delivery_date", "delivery_date"),
        Index("ix_dns_po_id", "po_id"),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=True)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[DeliveryNoteStatus] = mapped_column(
        String(30),
        default=DeliveryNoteStatus.DRAFT,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    source_system: Mapped[str] = mapped_column(String(50), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="dn",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.line_number",
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="delivery_notes",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}: {self.vendor_name} - {self.total_amount}>"
