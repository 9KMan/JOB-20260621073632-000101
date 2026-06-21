// src/services/matching.py
"""3-Way Matching engine service."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.match import (
    MatchRecord,
    MatchConfirmation,
    MatchType,
    MatchStatus,
    MatchResult,
)
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.models.balance import BalanceLedger, BalanceType
from src.schemas.match import MatchConfirmationCreate


class MatchingService:
    """
    3-Way Matching Engine.
    
    Layer 1: Anchoring - Uses PO as single source of truth
    Layer 2: Cascade Matching - Invoice↔PO, DN↔PO, Invoice↔DN
    Layer 3: Balance Resolution - Tracks partial matches
    """
    
    WEIGHT_LINE_LEVEL = Decimal("0.70")
    WEIGHT_AMOUNT = Decimal("0.20")
    WEIGHT_DATE = Decimal("0.10")
    
    AUTO_APPROVE_THRESHOLD = Decimal("95.00")
    HUMAN_REVIEW_THRESHOLD = Decimal("70.00")
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_open_pos(
        self,
        supplier_id: str,
        po_reference: Optional[str] = None,
    ) -> list[PurchaseOrder]:
        """Get open purchase orders for a supplier."""
        query = select(PurchaseOrder).options(
            selectinload(PurchaseOrder.lines)
        ).where(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_([
                    POStatus.APPROVED,
                    POStatus.PARTIALLY_RECEIVED,
                ])
            )
        )
        
        if po_reference:
            query = query.where(PurchaseOrder.po_number == po_reference)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _calculate_quantity_score(
        self,
        qty1: Decimal,
        qty2: Decimal,
    ) -> Decimal:
        """Calculate quantity match score (0-100)."""
        if qty1 == Decimal("0") and qty2 == Decimal("0"):
            return Decimal("100.00")
        if qty1 == Decimal("0") or qty2 == Decimal("0"):
            return Decimal("0.00")
        
        ratio = min(qty1, qty2) / max(qty1, qty2)
        return ratio * Decimal("100.00")
    
    async def _calculate_amount_score(
        self,
        amt1: Decimal,
        amt2: Decimal,
    ) -> Decimal:
        """Calculate amount match score (0-100)."""
        if amt1 == Decimal("0") and amt2 == Decimal("0"):
            return Decimal("100.00")
        if amt1 == Decimal("0") or amt2 == Decimal("0"):
            return Decimal("0.00")
        
        ratio = min(amt1, amt2) / max(amt1, amt2)
        return ratio * Decimal("100.00")
    
    async def _calculate_date_score(
        self,
        date1: str,
        date2: str,
        tolerance_days: int = 7,
    ) -> Decimal:
        """Calculate date match score (0-100)."""
        try:
            from datetime import datetime, timedelta
            
            d1 = datetime.strptime(date1, "%Y-%m-%d")
            d2 = datetime.strptime(date2, "%Y-%m-%d")
            diff = abs((d1 - d2).days)
            
            if diff == 0:
                return Decimal("100.00")
            elif diff <= tolerance_days:
                return Decimal("100.00") - Decimal(str(diff * 5))
            else:
                max_diff = 30
                score = max(Decimal("0.00"), Decimal("100.00") - Decimal(str((diff - tolerance_days) * 3)))
                return score
        except (ValueError, TypeError):
            return Decimal("50.00")
    
    async def _match_line_level(
        self,
        lines1: list,
        lines2: list,
    ) -> tuple[Decimal, dict]:
        """
        Match lines at line level.
        Returns score and match details.
        """
        total_score = Decimal("0.00")
        matched_lines = []
        
        lines2_remaining = {line.line_number: line for line in lines2}
        
        for line1 in lines1:
            best_match = None
            best_score = Decimal("0.00")
            
            for line2_num, line2 in lines2_remaining.items():
                score = Decimal("0.00")
                
                if line1.sku and line2.sku and line1.sku == line2.sku:
                    score += Decimal("40.00")
                
                desc_match = self._calculate_text_similarity(
                    line1.description.lower(),
                    line2.description.lower(),
                )
                score += desc_match * Decimal("30.00")
                
                qty_score = await self._calculate_quantity_score(
                    line1.quantity,
                    line2.quantity,
                )
                score += qty_score * Decimal("30.00")
                
                if score > best_score:
                    best_score = score
                    best_match = line2_num
            
            if best_match and best_score > Decimal("50.00"):
                total_score += best_score
                matched_lines.append({
                    "line1_id": line1.id,
                    "line2_id": lines2_remaining[best_match].id,
                    "score": float(best_score),
                })
                del lines2_remaining[best_match]
        
        if matched_lines:
            avg_score = total_score / Decimal(str(len(lines1)))
        else:
            avg_score = Decimal("0.00")
        
        return avg_score, {"matched_lines": matched_lines}
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> Decimal:
        """Calculate text similarity score."""
        if text1 == text2:
            return Decimal("1.00")
        if text1 in text2 or text2 in text1:
            return Decimal("0.80")
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return Decimal("0.00")
        
        intersection = words1 & words2
        union = words1 | words2
        
        return Decimal(str(len(intersection) / len(union)))
    
    async def _determine_match_result(
        self,
        variance_amount: Decimal,
        variance_quantity: Decimal,
        tolerance_pct: Decimal = Decimal("0.05"),
        tolerance_abs: Decimal = Decimal("10.00"),
    ) -> MatchResult:
        """Determine match result based on variance."""
        if variance_amount == Decimal("0") and variance_quantity == Decimal("0"):
            return MatchResult.EXACT
        
        if variance_amount <= tolerance_abs and variance_quantity <= Decimal("0.01"):
            return MatchResult.EXACT
        
        po_total = Decimal("100.00")
        variance_pct = abs(variance_amount) / po_total if po_total else Decimal("0")
        
        if variance_pct <= tolerance_pct:
            if variance_amount > 0:
                return MatchResult.OVER
            else:
                return MatchResult.UNDER
        else:
            return MatchResult.PARTIAL
    
    async def _determine_status(self, total_score: Decimal) -> MatchStatus:
        """Determine match status based on score."""
        if total_score >= self.AUTO_APPROVE_THRESHOLD:
            return MatchStatus.AUTO_CONFIRMED
        elif total_score >= self.HUMAN_REVIEW_THRESHOLD:
            return MatchStatus.HUMAN_REVIEW
        else:
            return MatchStatus.PENDING
    
    async def match_invoice_po(
        self,
        invoice: Invoice,
        po: PurchaseOrder,
    ) -> MatchRecord:
        """Match invoice against purchase order (Layer 2)."""
        line_score, line_details = await self._match_line_level(
            invoice.lines,
            po.lines,
        )
        
        amount_score = await self._calculate_amount_score(
            invoice.total_amount,
            po.total_amount,
        )
        
        date_score = await self._calculate_date_score(
            invoice.invoice_date,
            po.order_date,
        )
        
        total_score = (
            line_score * self.WEIGHT_LINE_LEVEL +
            amount_score * self.WEIGHT_AMOUNT +
            date_score * self.WEIGHT_DATE
        )
        
        variance_amount = invoice.total_amount - po.total_amount
        
        match_result = await self._determine_match_result(variance_amount, Decimal("0"))
        status = await self._determine_status(total_score)
        
        match_record = MatchRecord(
            match_type=MatchType.INVOICE_PO,
            invoice_id=invoice.id,
            purchase_order_id=po.id,
            line_match_details=line_details,
            quantity_match_score=line_score,
            amount_match_score=amount_score,
            date_match_score=date_score,
            total_score=total_score,
            match_result=match_result,
            status=status,
            variance_amount=variance_amount,
            variance_quantity=Decimal("0"),
        )
        
        self.db.add(match_record)
        await self.db.flush()
        
        return match_record
    
    async def match_delivery_po(
        self,
        dn: DeliveryNote,
        po: PurchaseOrder,
    ) -> MatchRecord:
        """Match delivery note against purchase order (Layer 2)."""
        line_score, line_details = await self._match_line_level(
            dn.lines,
            po.lines,
        )
        
        date_score = await self._calculate_date_score(
            dn.delivery_date,
            po.expected_delivery_date or po.order_date,
        )
        
        total_score = line_score * Decimal("0.90") + date_score * Decimal("0.10")
        
        variance_quantity = Decimal("0")
        for dn_line in dn.lines:
            for po_line in po.lines:
                if dn_line.sku == po_line.sku:
                    variance_quantity += dn_line.quantity - po_line.quantity
        
        match_result = await self._determine_match_result(Decimal("0"), variance_quantity)
        status = await self._determine_status(total_score)
        
        match_record = MatchRecord(
            match_type=MatchType.DELIVERY_PO,
            delivery_note_id=dn.id,
            purchase_order_id=po.id,
            line_match_details=line_details,
            quantity_match_score=line_score,
            amount_match_score=Decimal("100.00"),
            date_match_score=date_score,
            total_score=total_score,
            match_result=match_result,
            status=status,
            variance_amount=Decimal("0"),
            variance_quantity=variance_quantity,
        )
        
        self.db.add(match_record)
        await self.db.flush()
        
        return match_record
    
    async def match_invoice_delivery(
        self,
        invoice: Invoice,
        dn: DeliveryNote,
    ) -> MatchRecord:
        """Match invoice against delivery note (Layer 2)."""
        line_score, line_details = await self._match_line_level(
            invoice.lines,
            dn.lines,
        )
        
        amount_score = await self._calculate_amount_score(
            invoice.total_amount,
            dn.total_amount,
        )
        
        date_score = await self._calculate_date_score(
            invoice.invoice_date,
            dn.delivery_date,
        )
        
        total_score = (
            line_score * self.WEIGHT_LINE_LEVEL +
            amount_score * self.WEIGHT_AMOUNT +
            date_score * self.WEIGHT_DATE
        )
        
        variance_amount = invoice.total_amount - dn.total_amount
        match_result = await self._determine_match_result(variance_amount, Decimal("0"))
        status = await self._determine_status(total_score)
        
        match_record = MatchRecord(
            match_type=MatchType.INVOICE_DELIVERY,
            invoice_id=invoice.id,
            delivery_note_id=dn.id,
            line_match_details=line_details,
            quantity_match_score=line_score,
            amount_match_score=amount_score,
            date_match_score=date_score,
            total_score=total_score,
            match_result=match_result,
            status=status,
            variance_amount=variance_amount,
            variance_quantity=Decimal("0"),
        )
        
        self.db.add(match_record)
        await self.db.flush()
        
        return match_record
    
    async def perform_three_way_match(
        self,
        invoice: Invoice,
        po: PurchaseOrder,
        dn: DeliveryNote,
    ) -> tuple[MatchRecord, list[MatchRecord]]:
        """
        Perform full 3-way match.
        Returns the 3-way match record and all component matches.
        """
        invoice_po_match = await self.match_invoice_po(invoice, po)
        delivery_po_match = await self.match_delivery_po(dn, po)
        invoice_dn_match = await self.match_invoice_delivery(invoice, dn)
        
        total_score = (
            invoice_po_match.total_score +
            delivery_po_match.total_score +
            invoice_dn_match.total_score
        ) / Decimal("3")
        
        variance_amount = abs(invoice.total_amount - po.total_amount) + abs(dn.total_amount - po.total_amount)
        
        three_way_record = MatchRecord(
            match_type=MatchType.THREE_WAY,
            invoice_id=invoice.id,
            purchase_order_id=po.id,
            delivery_note_id=dn.id,
            line_match_details={
                "invoice_po_score": float(invoice_po_match.total_score),
                "delivery_po_score": float(delivery_po_match.total_score),
                "invoice_dn_score": float(invoice_dn_match.total_score),
            },
            quantity_match_score=total_score,
            amount_match_score=total_score,
            date_match_score=total_score,
            total_score=total_score,
            match_result=MatchResult.EXACT if variance_amount == 0 else MatchResult.PARTIAL,
            status=await self._determine_status(total_score),
            variance_amount=variance_amount,
            variance_quantity=Decimal("0"),
        )
        
        self.db.add(three_way_record)
        await self.db.flush()
        
        await self.db.commit()
        
        return three_way_record, [invoice_po_match, delivery_po_match, invoice_dn_match]
    
    async def find_possible_matches(
        self,
        invoice: Invoice,
    ) -> list[dict]:
        """Find all possible PO matches for an invoice (Layer 1 - Anchoring)."""
        pos = await self._get_open_pos(
            invoice.supplier_id,
            invoice.po_reference,
        )
        
        matches = []
        for po in pos:
            line_score, _ = await self._match_line_level(invoice.lines, po.lines)
            amount_score = await self._calculate_amount_score(
                invoice.total_amount,
                po.total_amount,
            )
            
            combined_score = (
                line_score * self.WEIGHT_LINE_LEVEL +
                amount_score * self.WEIGHT_AMOUNT
            )
            
            matches.append({
                "po": po,
                "score": combined_score,
                "line_score": line_score,
                "amount_score": amount_score,
            })
        
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches
    
    async def confirm_match(
        self,
        confirmation: MatchConfirmationCreate,
        user_id: UUID,
    ) -> Optional[MatchRecord]:
        """Confirm or reject a match (human review feedback)."""
        result = await self.db.execute(
            select(MatchRecord).where(MatchRecord.id == confirmation.match_record_id)
        )
        match_record = result.scalar_one_or_none()
        
        if not match_record:
            return None
        
        db_confirmation = MatchConfirmation(
            match_record_id=confirmation.match_record_id,
            user_id=user_id,
            decision=confirmation.decision,
            notes=confirmation.notes,
        )
        self.db.add(db_confirmation)
        
        match_record.status = confirmation.decision
        
        await self.db.commit()
        await self.db.refresh(match_record)
        
        return match_record
    
    async def get_match_record(self, match_id: UUID) -> Optional[MatchRecord]:
        """Get match record by ID."""
        result = await self.db.execute(
            select(MatchRecord)
            .options(selectinload(MatchRecord.confirmations))
            .where(MatchRecord.id == match_id)
        )
        return result.scalar_one_or_none()
    
    async def get_matches_for_invoice(self, invoice_id: UUID) -> list[MatchRecord]:
        """Get all matches for an invoice."""
        result = await self.db.execute(
            select(MatchRecord)
            .where(MatchRecord.invoice_id == invoice_id)
            .order_by(MatchRecord.total_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_matches_for_po(self, po_id: UUID) -> list[MatchRecord]:
        """Get all matches for a purchase order."""
        result = await self.db.execute(
            select(MatchRecord)
            .where(MatchRecord.purchase_order_id == po_id)
            .order_by(MatchRecord.total_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_matches_for_dn(self, dn_id: UUID) -> list[MatchRecord]:
        """Get all matches for a delivery note."""
        result = await self.db.execute(
            select(MatchRecord)
            .where(MatchRecord.delivery_note_id == dn_id)
            .order_by(MatchRecord.total_score.desc())
        )
        return list(result.scalars().all())
