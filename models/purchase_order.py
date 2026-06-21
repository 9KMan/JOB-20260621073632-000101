// models/purchase_order.py
// models/purchase_order.py
"""Purchase Order and PurchaseOrderLine SQLAlchemy models."""

from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header model."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_supplier_number", "supplier_number"),
        Index("ix_purchase_orders_order_date", "order_date"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_created_at", "created_at"),
        Index("ix_purchase_orders_external_reference", "external_reference"),
        {
            "schema": "public",
        },
    )

    # PO identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Purchase order number",
    )
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="External system reference (ERP)",
    )
    release_number: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="PO release number for blanket orders",
    )

    # Supplier information
    supplier_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Internal supplier identifier",
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Supplier name",
    )
    supplier_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Supplier account number",
    )

    # Company/Legal Entity
    company_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Company code",
    )
    business_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Business unit code",
    )

    # Dates
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date PO was created/sent",
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Requested delivery date",
    )
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="PO expiration date",
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total PO amount including tax",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax amount",
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Net PO amount before tax",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        doc="Purchase order status",
    )
    is_ blanket_order: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating blanket order",
    )
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating supplier acknowledgment",
    )

    # Terms
    payment_terms: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Payment terms code",
    )
    delivery_terms: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Delivery/incoterms",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="PO description or notes",
    )

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # User tracking
    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who created the PO",
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User who approved the PO",
    )

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, status={self.status})>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order line item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po_id", "po_id"),
        Index("ix_purchase_order_lines_line_number", "line_number"),
        Index("ix_purchase_order_lines_product_code", "product_code"),
        Index("ix_purchase_order_lines_schedule_line", "schedule_line_number"),
        {
            "schema": "public",
        },
    )

    # Parent reference
    po_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent purchase order ID",
    )

    # Line identification
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item sequence number",
    )
    schedule_line_number: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Schedule line number for delivery schedule",
    )
    external_line_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="External system line reference",
    )

    # Product/Service information
    product_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Product or service code",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Line item description",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Ordered quantity",
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Total received quantity",
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
        doc="Total invoiced quantity",
    )
    unit_of_measure: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measure",
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total line amount",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Tax rate percentage",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Line tax amount",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LineStatus.PENDING,
        doc="Line status",
    )

    # Delivery schedule
    required_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Required delivery date",
    )
    promised_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Promised delivery date from supplier",
    )

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional metadata as JSON",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    balance_ledger: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.quantity - self.received_quantity

    @property
    def remaining_to_invoice(self) -> Decimal:
        """Calculate remaining quantity to invoice."""
        return self.received_quantity - self.invoiced_quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, po_id={self.po_id}, line={self.line_number})>"
