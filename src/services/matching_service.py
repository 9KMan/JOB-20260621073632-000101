// src/services/matching_service.py
"""3-Way Matching Engine Service."""
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.config import get_settings
from src.models.balance import BalanceLedger, BalanceLedgerEntry
from src.models.delivery_note import DeliveryNote, DeliveryNoteLineItem
from src.models.invoice import Invoice, InvoiceLineItem
from src.models.match import Match, MatchCrossReference
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from src.schemas.match import MatchLineDetail

settings = get_settings()
logger = logging.getLogger(__name__)


class MatchingService:
    """Service for 3-way matching operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.line_weight = settings.MATCH_WEIGHT_LINE_LEVEL
        self.amount_weight = settings.MATCH_WEIGHT_AMOUNT
        self.date_weight = settings.MATCH_WEIGHT_DATE
        self.auto_approve_threshold = settings.AUTO_APPROVE_THRESHOLD
        self.human_review_threshold = settings.HUMAN_REVIEW_THRESHOLD
    
    async def get_po_line_items(self, po_id: UUID) -> list[PurchaseOrderLineItem]:
        """Get line items for a purchase order."""
        result = await self.db.execute(
            select(PurchaseOrderLineItem)
            .where(PurchaseOrderLineItem.purchase_order_id == po_id)
            .order_by(PurchaseOrderLineItem.line_number)
        )
        return list(result.scalars().all())
    
    async def get_invoice_line_items(self, invoice_id: UUID) -> list[InvoiceLineItem]:
        """Get line items for an invoice."""
        result = await self.db.execute(
            select(InvoiceLineItem)
            .where(InvoiceLineItem.invoice_id == invoice_id)
            .order_by(InvoiceLineItem.line_number)
        )
        return list(result.scalars().all())
    
    async def get_dn_line_items(self, dn_id: UUID) -> list[DeliveryNoteLineItem]:
        """Get line items for a delivery note."""
        result = await self.db.execute(
            select(DeliveryNoteLineItem)
            .where(DeliveryNoteLineItem.delivery_note_id == dn_id)
            .order_by(DeliveryNoteLineItem.line_number)
        )
        return list(result.scalars().all())
    
    def _calculate_line_level_score(
        self,
        source_items: list,
        target_items: list,
        is_partial: bool = False,
    ) -> tuple[Decimal, list[MatchLineDetail]]:
        """Calculate line-level matching score between two document line items."""
        line_matches: list[MatchLineDetail] = []
        total_lines = len(source_items) if not is_partial else max(len(source_items), len(target_items))
        
        if total_lines == 0:
            return Decimal("1.0"), []
        
        matched_lines = 0
        source_by_code = {item.item_code: item for item in source_items}
        target_by_code = {item.item_code: item for item in target_items}
        
        for source_item in source_items:
            target_item = target_by_code.get(source_item.item_code)
            if target_item:
                qty_match = abs(source_item.quantity - target_item.quantity) < Decimal("0.001")
                price_match = abs(source_item.unit_price - target_item.unit_price) < Decimal("0.0001")
                
                if qty_match and price_match:
                    matched_lines += 1
                    line_score = Decimal("1.0")
                elif qty_match or price_match:
                    matched_lines += Decimal("0.5")
                    line_score = Decimal("0.75")
                else:
                    qty_variance = abs(source_item.quantity - target_item.quantity)
                    price_variance = abs(source_item.unit_price - target_item.unit_price)
                    line_score = self._calculate_item_score(
                        source_item, target_item, qty_variance, price_variance
                    )
                    matched_lines += line_score
            else:
                line_score = Decimal("0.0")
                line_matches.append(
                    MatchLineDetail(
                        source_line_number=source_item.line_number,
                        target_line_number=0,
                        source_item_code=source_item.item_code,
                        target_item_code="",
                        quantity_match=False,
                        price_match=False,
                        quantity_variance=source_item.quantity,
                        price_variance=source_item.unit_price,
                        line_score=line_score,
                    )
                )
                continue
            
            qty_variance = abs(source_item.quantity - target_item.quantity) if target_item else source_item.quantity
            price_variance = abs(source_item.unit_price - target_item.unit_price) if target_item else source_item.unit_price
            
            line_matches.append(
                MatchLineDetail(
                    source_line_number=source_item.line_number,
                    target_line_number=target_item.line_number if target_item else 0,
                    source_item_code=source_item.item_code,
                    target_item_code=target_item.item_code if target_item else "",
                    quantity_match=qty_match,
                    price_match=price_match,
                    quantity_variance=qty_variance,
                    price_variance=price_variance,
                    line_score=line_score,
                )
            )
        
        score = Decimal(str(matched_lines)) / Decimal(str(total_lines)) if total_lines > 0 else Decimal("1.0")
        return min(score, Decimal("1.0")), line_matches
    
    def _calculate_item_score(
        self,
        source_item,
        target_item,
        qty_variance: Decimal,
        price_variance: Decimal,
    ) -> Decimal:
        """Calculate score for a single item match."""
        max_qty = max(source_item.quantity, target_item.quantity)
        max_price = max(source_item.unit_price, target_item.unit_price)
        
        qty_score = Decimal("1.0") - (qty_variance / max_qty) if max_qty > 0 else Decimal("1.0")
        price_score = Decimal("1.0") - (price_variance / max_price) if max_price > 0 else Decimal("1.0")
        
        return (qty_score * Decimal("0.6") + price_score * Decimal("0.4")).quantize(Decimal("0.0001"))
    
    def _calculate_amount_score(
        self,
        source_amount: Decimal,
        target_amount: Decimal,
    ) -> Decimal:
        """Calculate amount matching score."""
        if source_amount == Decimal("0"):
            return Decimal("1.0") if target_amount == Decimal("0") else Decimal("0.0")
        
        variance = abs(source_amount - target_amount)
        score = Decimal("1.0") - (variance / source_amount)
        return max(Decimal("0.0"), min(score, Decimal("1.0"))).quantize(Decimal("0.0001"))
    
    def _calculate_date_score(
        self,
        source_date: date,
        target_date: date,
        tolerance_days: int = 7,
    ) -> Decimal:
        """Calculate date matching score with tolerance."""
        days_diff = abs((source_date - target_date).days)
        if days_diff <= tolerance_days:
            return Decimal("1.0")
        elif days_diff <= tolerance_days * 2:
            return Decimal("0.8")
        elif days_diff <= tolerance_days * 3:
            return Decimal("0.6")
        else:
            return max(Decimal("0.0"), Decimal("0.5") - Decimal(str(days_diff - 21)) / Decimal("100"))
    
    def _determine_decision(self, overall_score: Decimal) -> tuple[str, str]:
        """Determine match decision based on score."""
        if overall_score >= self.auto_approve_threshold:
            return "CONFIRMED", "AUTO_APPROVE"
        elif overall_score >= self.human_review_threshold:
            return "PENDING", "HUMAN_REVIEW"
        else:
            return "REJECTED", "DISPUTE"
    
    async def match_invoice_to_po(self, invoice_id: UUID, po_id: UUID) -> Match:
        """Match an invoice against a purchase order."""
        invoice = await self.db.get(Invoice, invoice_id)
        po = await self.db.get(PurchaseOrder, po_id)
        
        if not invoice or not po:
            raise ValueError("Invoice or PO not found")
        
        invoice_items = await self.get_invoice_line_items(invoice_id)
        po_items = await self.get_po_line_items(po_id)
        
        line_score, line_matches = self._calculate_line_level_score(invoice_items, po_items)
        amount_score = self._calculate_amount_score(invoice.total_amount, po.total_amount)
        date_score = self._calculate_date_score(invoice.invoice_date, po.order_date)
        
        overall_score = (
            line_score * Decimal(str(self.line_weight)) +
            amount_score * Decimal(str(self.amount_weight)) +
            date_score * Decimal(str(self.date_weight))
        ).quantize(Decimal("0.0001"))
        
        match_status, decision = self._determine_decision(overall_score)
        variance = abs(invoice.total_amount - po.total_amount)
        
        match = Match(
            invoice_id=invoice_id,
            purchase_order_id=po_id,
            match_type="INVOICE_PO",
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            overall_score=overall_score,
            match_status=match_status,
            decision=decision,
            invoice_amount=invoice.total_amount,
            po_amount=po.total_amount,
            variance_amount=variance,
            line_matches=[lm.model_dump() for lm in line_matches],
        )
        
        self.db.add(match)
        await self.db.flush()
        await self.db.refresh(match)
        return match
    
    async def match_dn_to_po(self, dn_id: UUID, po_id: UUID) -> Match:
        """Match a delivery note against a purchase order."""
        dn = await self.db.get(DeliveryNote, dn_id)
        po = await self.db.get(PurchaseOrder, po_id)
        
        if not dn or not po:
            raise ValueError("Delivery Note or PO not found")
        
        dn_items = await self.get_dn_line_items(dn_id)
        po_items = await self.get_po_line_items(po_id)
        
        line_score, line_matches = self._calculate_line_level_score(dn_items, po_items)
        amount_score = self._calculate_amount_score(dn.total_amount, po.total_amount)
        date_score = self._calculate_date_score(dn.delivery_date, po.order_date)
        
        overall_score = (
            line_score * Decimal(str(self.line_weight)) +
            amount_score * Decimal(str(self.amount_weight)) +
            date_score * Decimal(str(self.date_weight))
        ).quantize(Decimal("0.0001"))
        
        match_status, decision = self._determine_decision(overall_score)
        variance = abs(dn.total_amount - po.total_amount)
        
        match = Match(
            delivery_note_id=dn_id,
            purchase_order_id=po_id,
            match_type="DN_PO",
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            overall_score=overall_score,
            match_status=match_status,
            decision=decision,
            po_amount=po.total_amount,
            dn_amount=dn.total_amount,
            variance_amount=variance,
            line_matches=[lm.model_dump() for lm in line_matches],
        )
        
        self.db.add(match)
        await self.db.flush()
        await self.db.refresh(match)
        return match
    
    async def match_invoice_to_dn(self, invoice_id: UUID, dn_id: UUID) -> Match:
        """Match an invoice against a delivery note."""
        invoice = await self.db.get(Invoice, invoice_id)
        dn = await self.db.get(DeliveryNote, dn_id)
        
        if not invoice or not dn:
            raise ValueError("Invoice or Delivery Note not found")
        
        invoice_items = await self.get_invoice_line_items(invoice_id)
        dn_items = await self.get_dn_line_items(dn_id)
        
        line_score, line_matches = self._calculate_line_level_score(invoice_items, dn_items)
        amount_score = self._calculate_amount_score(invoice.total_amount, dn.total_amount)
        date_score = self._calculate_date_score(invoice.invoice_date, dn.delivery_date)
        
        overall_score = (
            line_score * Decimal(str(self.line_weight)) +
            amount_score * Decimal(str(self.amount_weight)) +
            date_score * Decimal(str(self.date_weight))
        ).quantize(Decimal("0.0001"))
        
        match_status, decision = self._determine_decision(overall_score)
        variance = abs(invoice.total_amount - dn.total_amount)
        
        match = Match(
            invoice_id=invoice_id,
            delivery_note_id=dn_id,
            match_type="INVOICE_DN",
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            overall_score=overall_score,
            match_status=match_status,
            decision=decision,
            invoice_amount=invoice.total_amount,
            dn_amount=dn.total_amount,
            variance_amount=variance,
            line_matches=[lm.model_dump() for lm in line_matches],
        )
        
        self.db.add(match)
        await self.db.flush()
        await self.db.refresh(match)
        return match
    
    async def perform_full_3way_match(
        self,
        invoice_id: UUID,
        dn_id: UUID,
        po_id: UUID,
    ) -> Match:
        """Perform complete 3-way matching between Invoice, DN, and PO."""
        invoice = await self.db.get(Invoice, invoice_id)
        dn = await self.db.get(DeliveryNote, dn_id)
        po = await self.db.get(PurchaseOrder, po_id)
        
        if not all([invoice, dn, po]):
            raise ValueError("One or more documents not found")
        
        invoice_items = await self.get_invoice_line_items(invoice_id)
        dn_items = await self.get_dn_line_items(dn_id)
        po_items = await self.get_po_line_items(po_id)
        
        inv_po_score, _ = self._calculate_line_level_score(invoice_items, po_items)
        inv_dn_score, _ = self._calculate_line_level_score(invoice_items, dn_items)
        dn_po_score, _ = self._calculate_line_level_score(dn_items, po_items)
        
        line_score = (inv_po_score + inv_dn_score + dn_po_score) / Decimal("3")
        
        invoice_total = invoice.total_amount
        po_total = po.total_amount
        dn_total = dn.total_amount
        
        avg_expected = (po_total + dn_total) / Decimal("2")
        amount_score = self._calculate_amount_score(invoice_total, avg_expected)
        
        invoice_date = invoice.invoice_date
        dn_date = dn.delivery_date
        po_date = po.order_date
        
        date_score = (
            self._calculate_date_score(invoice_date, po_date) +
            self._calculate_date_score(invoice_date, dn_date) +
            self._calculate_date_score(dn_date, po_date)
        ) / Decimal("3")
        
        overall_score = (
            line_score * Decimal(str(self.line_weight)) +
            amount_score * Decimal(str(self.amount_weight)) +
            date_score * Decimal(str(self.date_weight))
        ).quantize(Decimal("0.0001"))
        
        match_status, decision = self._determine_decision(overall_score)
        
        max_amount = max(invoice_total, po_total, dn_total)
        variance = max_amount - min(invoice_total, po_total, dn_total)
        
        match = Match(
            invoice_id=invoice_id,
            delivery_note_id=dn_id,
            purchase_order_id=po_id,
            match_type="FULL_3WAY",
            line_level_score=line_score.quantize(Decimal("0.0001")),
            amount_score=amount_score,
            date_score=date_score.quantize(Decimal("0.0001")),
            overall_score=overall_score,
            match_status=match_status,
            decision=decision,
            invoice_amount=invoice_total,
            po_amount=po_total,
            dn_amount=dn_total,
            variance_amount=variance,
        )
        
        self.db.add(match)
        await self.db.flush()
        await self.db.refresh(match)
        return match
    
    async def find_po_for_document(
        self,
        supplier_id: UUID,
        document_date: date,
        amount: Decimal,
    ) -> Optional[PurchaseOrder]:
        """Find the best matching PO for anchoring a document."""
        date_tolerance = timedelta(days=30)
        min_date = document_date - date_tolerance
        max_date = document_date + date_tolerance
        
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.line_items))
            .where(
                and_(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.status == "OPEN",
                    PurchaseOrder.is_deleted == False,
                    PurchaseOrder.order_date >= min_date,
                    PurchaseOrder.order_date <= max_date,
                )
            )
            .order_by(PurchaseOrder.order_date.desc())
        )
        
        pos = list(result.scalars().all())
        
        best_po = None
        best_score = Decimal("0.0")
        
        for po in pos:
            amount_score = self._calculate_amount_score(amount, po.total_amount)
            date_score = self._calculate_date_score(document_date, po.order_date)
            score = (amount_score * Decimal("0.7") + date_score * Decimal("0.3")).quantize(Decimal("0.0001"))
            
            if score > best_score:
                best_score = score
                best_po = po
        
        return best_po
    
    async def get_match_by_id(self, match_id: UUID) -> Optional[Match]:
        """Get a match by ID."""
        return await self.db.get(Match, match_id)
    
    async def get_matches_for_invoice(self, invoice_id: UUID) -> list[Match]:
        """Get all matches for an invoice."""
        result = await self.db.execute(
            select(Match)
            .where(Match.invoice_id == invoice_id, Match.is_deleted == False)
            .order_by(Match.overall_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_matches_for_dn(self, dn_id: UUID) -> list[Match]:
        """Get all matches for a delivery note."""
        result = await self.db.execute(
            select(Match)
            .where(Match.delivery_note_id == dn_id, Match.is_deleted == False)
            .order_by(Match.overall_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_matches_for_po(self, po_id: UUID) -> list[Match]:
        """Get all matches for a purchase order."""
        result = await self.db.execute(
            select(Match)
            .where(Match.purchase_order_id == po_id, Match.is_deleted == False)
            .order_by(Match.overall_score.desc())
        )
        return list(result.scalars().all())
