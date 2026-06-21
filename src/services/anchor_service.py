// src/services/anchor_service.py
"""Anchor Service - Layer 1 of 3-Way Matching.

Establishes deterministic anchoring by matching invoices and delivery notes
against open Purchase Orders as the single source of truth.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.models.invoice import Invoice, InvoiceLine
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine


class AnchorResult:
    """Result of anchoring a document to a Purchase Order."""

    def __init__(
        self,
        success: bool,
        purchase_order: Optional[PurchaseOrder] = None,
        match_confidence: Decimal = Decimal("0.00"),
        match_method: str = "none",
        message: str = "",
    ):
        self.success = success
        self.purchase_order = purchase_order
        self.match_confidence = match_confidence
        self.match_method = match_method
        self.message = message


class AnchorService:
    """Service for anchoring invoices and delivery notes to Purchase Orders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_purchase_order_for_invoice(
        self,
        supplier_id: UUID,
        invoice_number: str,
        invoice_date: date,
        total_amount: Decimal,
    ) -> AnchorResult:
        """Find and anchor a Purchase Order for an invoice.
        
        Matching strategy:
        1. Exact match on supplier_id + invoice_number reference
        2. Match on supplier_id + approximate amount (within 5%)
        3. Match on supplier_id + date range
        """
        # First, try exact match by supplier and reference
        po = await self._find_po_by_supplier_reference(supplier_id, invoice_number)
        if po:
            return AnchorResult(
                success=True,
                purchase_order=po,
                match_confidence=Decimal("100.00"),
                match_method="exact_reference",
                message=f"Matched PO {po.po_number} by reference",
            )

        # Try amount-based matching
        po = await self._find_po_by_amount(supplier_id, total_amount)
        if po:
            return AnchorResult(
                success=True,
                purchase_order=po,
                match_confidence=Decimal("90.00"),
                match_method="amount_match",
                message=f"Matched PO {po.po_number} by amount",
            )

        # Try to find any open PO for supplier
        po = await self._find_open_po_by_supplier(supplier_id)
        if po:
            return AnchorResult(
                success=True,
                purchase_order=po,
                match_confidence=Decimal("70.00"),
                match_method="supplier_match",
                message=f"Matched PO {po.po_number} by supplier",
            )

        return AnchorResult(
            success=False,
            message="No matching Purchase Order found",
        )

    async def find_purchase_order_for_delivery_note(
        self,
        supplier_id: UUID,
        dn_number: str,
        delivery_date: date,
        total_amount: Decimal,
    ) -> AnchorResult:
        """Find and anchor a Delivery Note to a Purchase Order.
        
        Matching strategy:
        1. Exact match on supplier_id + dn_number reference
        2. Match on supplier_id + date range
        """
        # Try exact match by supplier and reference
        po = await self._find_po_by_supplier_reference(supplier_id, dn_number)
        if po:
            return AnchorResult(
                success=True,
                purchase_order=po,
                match_confidence=Decimal("100.00"),
                match_method="exact_reference",
                message=f"Matched PO {po.po_number} by reference",
            )

        # Try date-based matching
        po = await self._find_po_by_date_range(supplier_id, delivery_date)
        if po:
            return AnchorResult(
                success=True,
                purchase_order=po,
                match_confidence=Decimal("80.00"),
                match_method="date_range",
                message=f"Matched PO {po.po_number} by date",
            )

        # Fall back to any open PO
        po = await self._find_open_po_by_supplier(supplier_id)
        if po:
            return AnchorResult(
                success=True,
                purchase_order=po,
                match_confidence=Decimal("60.00"),
                match_method="supplier_fallback",
                message=f"Matched PO {po.po_number} by supplier",
            )

        return AnchorResult(
            success=False,
            message="No matching Purchase Order found",
        )

    async def anchor_invoice_to_po(
        self,
        invoice: Invoice,
        purchase_order: PurchaseOrder,
    ) -> Invoice:
        """Anchor an invoice to a Purchase Order."""
        invoice.purchase_order_id = purchase_order.id
        await self.db.flush()
        return invoice

    async def anchor_delivery_note_to_po(
        self,
        delivery_note: DeliveryNote,
        purchase_order: PurchaseOrder,
    ) -> DeliveryNote:
        """Anchor a delivery note to a Purchase Order."""
        delivery_note.purchase_order_id = purchase_order.id
        await self.db.flush()
        return delivery_note

    async def _find_po_by_supplier_reference(
        self,
        supplier_id: UUID,
        reference: str,
    ) -> Optional[PurchaseOrder]:
        """Find a PO by supplier and reference number."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                and_(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.supplier_reference == reference,
                    PurchaseOrder.status.in_(["open", "partial"]),
                    PurchaseOrder.is_deleted == False,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _find_po_by_amount(
        self,
        supplier_id: UUID,
        amount: Decimal,
        tolerance: float = 0.05,
    ) -> Optional[PurchaseOrder]:
        """Find a PO by approximate amount match."""
        min_amount = amount * Decimal(str(1 - tolerance))
        max_amount = amount * Decimal(str(1 + tolerance))

        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                and_(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.total_amount >= min_amount,
                    PurchaseOrder.total_amount <= max_amount,
                    PurchaseOrder.status.in_(["open", "partial"]),
                    PurchaseOrder.is_deleted == False,
                )
            )
            .order_by(PurchaseOrder.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def _find_po_by_date_range(
        self,
        supplier_id: UUID,
        delivery_date: date,
    ) -> Optional[PurchaseOrder]:
        """Find a PO within expected delivery date range."""
        from datetime import timedelta

        min_date = delivery_date - timedelta(days=30)
        max_date = delivery_date + timedelta(days=30)

        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                and_(
                    PurchaseOrder.supplier_id == supplier_id,
                    or_(
                        PurchaseOrder.expected_delivery_date >= min_date,
                        PurchaseOrder.expected_delivery_date == None,
                    ),
                    PurchaseOrder.expected_delivery_date <= max_date,
                    PurchaseOrder.status.in_(["open", "partial"]),
                    PurchaseOrder.is_deleted == False,
                )
            )
            .order_by(PurchaseOrder.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def _find_open_po_by_supplier(self, supplier_id: UUID) -> Optional[PurchaseOrder]:
        """Find any open PO for a supplier."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(
                and_(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.status.in_(["open", "partial"]),
                    PurchaseOrder.is_deleted == False,
                )
            )
            .order_by(PurchaseOrder.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_po_with_lines(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get a Purchase Order with all its lines."""
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()
