// src/services/matching.py
"""3-Way Matching Engine service.

This service implements the 3-layer matching architecture:
- Layer 1: PO as single source of truth for anchoring
- Layer 2: Cascade matching (PO↔Invoice, DN↔PO, Invoice↔DN)
- Layer 3: Balance resolution for partial matches
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from src.models.balance import Balance, BalanceDirection, BalanceType
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
from src.models.invoice import Invoice, InvoiceLine
from src.models.match import Match, MatchStatus, MatchType
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from src.schemas.match import MatchDecision, MatchResponse, MatchResultResponse

settings = get_settings()


@dataclass
class LineMatchResult:
    """Result of matching a single line."""
    po_line_id: Optional[UUID]
    invoice_line_id: Optional[UUID]
    dn_line_id: Optional[UUID]
    score: Decimal
    quantity_variance: Decimal
    price_variance: Decimal
    matched_quantity: Decimal
    matched_amount: Decimal


@dataclass
class MatchScore:
    """Overall match score breakdown."""
    line_level_score: Decimal = Decimal("0")
    amount_score: Decimal = Decimal("0")
    date_score: Decimal = Decimal("0")
    total_score: Decimal = Decimal("0")
    line_matches: list[LineMatchResult] = field(default_factory=list)


class MatchingService:
    """3-Way Matching Engine service."""

    # Tolerance for floating point comparisons
    AMOUNT_TOLERANCE = Decimal("0.01")
    QUANTITY_TOLERANCE = Decimal("0.001")
    DATE_TOLERANCE_DAYS = 7

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = settings

    async def match_invoice_to_po(
        self,
        invoice: Invoice,
        purchase_order: PurchaseOrder
    ) -> Optional[Match]:
        """Layer 1 & 2: Match invoice to purchase order."""
        score = await self._calculate_match_score(
            invoice=invoice,
            purchase_order=purchase_order
        )
        
        # Create match record
        match = Match(
            match_type=MatchType.PO_INVOICE,
            total_score=score.total_score,
            line_level_score=score.line_level_score,
            amount_score=score.amount_score,
            date_score=score.date_score,
            matched_amount=Decimal("0"),
            variance_amount=Decimal("0"),
            purchase_order_id=purchase_order.id,
            invoice_id=invoice.id,
            line_matches=[lm.__dict__ for lm in score.line_matches],
        )
        
        # Calculate matched and variance amounts
        matched_amount = sum(lm.matched_amount for lm in score.line_matches)
        match.matched_amount = matched_amount
        match.variance_amount = abs(invoice.total_amount - matched_amount)
        
        # Calculate variances
        variances = self._calculate_variances(score, invoice, purchase_order)
        match.quantity_variance = variances["quantity"]
        match.price_variance = variances["price"]
        match.date_variance_days = variances["date_days"]
        
        # Route to decision engine
        match.status = self._route_decision(score.total_score)
        
        self.db.add(match)
        await self.db.flush()
        
        # Update invoice with PO reference
        invoice.purchase_order_id = purchase_order.id
        
        return match

    async def match_delivery_to_po(
        self,
        delivery_note: DeliveryNote,
        purchase_order: PurchaseOrder
    ) -> Optional[Match]:
        """Layer 2: Match delivery note to purchase order."""
        score = await self._calculate_delivery_match_score(
            delivery_note=delivery_note,
            purchase_order=purchase_order
        )
        
        match = Match(
            match_type=MatchType.PO_DELIVERY,
            total_score=score.total_score,
            line_level_score=score.line_level_score,
            amount_score=Decimal("1.0"),  # DN typically doesn't have amounts
            date_score=score.date_score,
            matched_amount=Decimal("0"),
            variance_amount=Decimal("0"),
            purchase_order_id=purchase_order.id,
            delivery_note_id=delivery_note.id,
            line_matches=[lm.__dict__ for lm in score.line_matches],
        )
        
        # Calculate quantity match
        matched_qty = sum(lm.matched_quantity for lm in score.line_matches)
        match.matched_amount = matched_qty  # For DN, this is quantity
        
        # Route to decision engine
        match.status = self._route_decision(score.total_score)
        
        self.db.add(match)
        await self.db.flush()
        
        # Update delivery note with PO reference
        delivery_note.purchase_order_id = purchase_order.id
        
        return match

    async def match_three_way(
        self,
        invoice: Invoice,
        delivery_note: DeliveryNote,
        purchase_order: PurchaseOrder
    ) -> Optional[Match]:
        """Layer 2: Full 3-way match."""
        # Calculate individual scores
        invoice_po_score = await self._calculate_match_score(
            invoice=invoice,
            purchase_order=purchase_order
        )
        delivery_po_score = await self._calculate_delivery_match_score(
            delivery_note=delivery_note,
            purchase_order=purchase_order
        )
        
        # Weighted average for 3-way score
        total_score = (
            invoice_po_score.total_score * Decimal("0.5") +
            delivery_po_score.total_score * Decimal("0.5")
        )
        
        match = Match(
            match_type=MatchType.THREE_WAY,
            total_score=total_score,
            line_level_score=(
                invoice_po_score.line_level_score * Decimal("0.5") +
                delivery_po_score.line_level_score * Decimal("0.5")
            ),
            amount_score=invoice_po_score.amount_score,
            date_score=(
                invoice_po_score.date_score * Decimal("0.5") +
                delivery_po_score.date_score * Decimal("0.5")
            ),
            matched_amount=min(
                invoice.total_amount,
                delivery_note.total_quantity * self._get_avg_unit_price(purchase_order)
            ),
            variance_amount=abs(invoice.total_amount - delivery_note.total_quantity * self._get_avg_unit_price(purchase_order)),
            purchase_order_id=purchase_order.id,
            invoice_id=invoice.id,
            delivery_note_id=delivery_note.id,
        )
        
        # Route to decision engine
        match.status = self._route_decision(total_score)
        
        self.db.add(match)
        await self.db.flush()
        
        return match

    async def _calculate_match_score(
        self,
        invoice: Invoice,
        purchase_order: PurchaseOrder
    ) -> MatchScore:
        """Calculate match score between invoice and PO."""
        score = MatchScore()
        
        # Load lines
        await self.db.refresh(
            invoice,
            ["lines"]
        )
        await self.db.refresh(
            purchase_order,
            ["lines"]
        )
        
        invoice_lines = {il.line_number: il for il in invoice.lines}
        po_lines = {pl.line_number: pl for pl in purchase_order.lines}
        
        line_scores = []
        
        # Line-level matching (70% weight)
        for line_num, po_line in po_lines.items():
            if line_num in invoice_lines:
                inv_line = invoice_lines[line_num]
                line_score = self._calculate_line_score(po_line, inv_line)
                
                # Match quantity and amount
                matched_qty = min(po_line.quantity, inv_line.quantity)
                matched_amt = matched_qty * inv_line.unit_price
                
                line_scores.append(LineMatchResult(
                    po_line_id=po_line.id,
                    invoice_line_id=inv_line.id,
                    dn_line_id=None,
                    score=line_score,
                    quantity_variance=abs(po_line.quantity - inv_line.quantity),
                    price_variance=abs(po_line.unit_price - inv_line.unit_price),
                    matched_quantity=matched_qty,
                    matched_amount=matched_amt
                ))
            else:
                line_scores.append(LineMatchResult(
                    po_line_id=po_line.id,
                    invoice_line_id=None,
                    dn_line_id=None,
                    score=Decimal("0"),
                    quantity_variance=po_line.quantity,
                    price_variance=Decimal("0"),
                    matched_quantity=Decimal("0"),
                    matched_amount=Decimal("0")
                ))
        
        # Calculate line level score
        if line_scores:
            score.line_level_score = sum(ls.score for ls in line_scores) / len(line_scores)
        score.line_matches = line_scores
        
        # Amount score (20% weight)
        score.amount_score = self._calculate_amount_score(
            invoice.total_amount,
            purchase_order.total_amount,
            [ls.matched_amount for ls in line_scores]
        )
        
        # Date score (10% weight)
        score.date_score = self._calculate_date_score(
            invoice.invoice_date,
            purchase_order.order_date
        )
        
        # Total weighted score
        score.total_score = (
            score.line_level_score * Decimal(str(self.config.MATCH_WEIGHT_LINE_LEVEL)) +
            score.amount_score * Decimal(str(self.config.MATCH_WEIGHT_AMOUNT)) +
            score.date_score * Decimal(str(self.config.MATCH_WEIGHT_DATE))
        )
        
        return score

    async def _calculate_delivery_match_score(
        self,
        delivery_note: DeliveryNote,
        purchase_order: PurchaseOrder
    ) -> MatchScore:
        """Calculate match score between delivery note and PO."""
        score = MatchScore()
        
        # Load lines
        await self.db.refresh(delivery_note, ["lines"])
        await self.db.refresh(purchase_order, ["lines"])
        
        dn_lines = {dl.line_number: dl for dl in delivery_note.lines}
        po_lines = {pl.line_number: pl for pl in purchase_order.lines}
        
        line_scores = []
        
        for line_num, po_line in po_lines.items():
            if line_num in dn_lines:
                dn_line = dn_lines[line_num]
                line_score = self._calculate_quantity_score(
                    po_line.quantity,
                    dn_line.quantity
                )
                
                line_scores.append(LineMatchResult(
                    po_line_id=po_line.id,
                    invoice_line_id=None,
                    dn_line_id=dn_line.id,
                    score=line_score,
                    quantity_variance=abs(po_line.quantity - dn_line.quantity),
                    price_variance=Decimal("0"),
                    matched_quantity=min(po_line.quantity, dn_line.quantity),
                    matched_amount=Decimal("0")  # No amount for DN
                ))
            else:
                line_scores.append(LineMatchResult(
                    po_line_id=po_line.id,
                    invoice_line_id=None,
                    dn_line_id=None,
                    score=Decimal("0"),
                    quantity_variance=po_line.quantity,
                    price_variance=Decimal("0"),
                    matched_quantity=Decimal("0"),
                    matched_amount=Decimal("0")
                ))
        
        if line_scores:
            score.line_level_score = sum(ls.score for ls in line_scores) / len(line_scores)
        score.line_matches = line_scores
        
        # For DN-PO, quantity is the main factor
        score.amount_score = Decimal("1.0")
        
        # Date score
        score.date_score = self._calculate_date_score(
            delivery_note.delivery_date,
            purchase_order.expected_delivery_date or purchase_order.order_date
        )
        
        score.total_score = (
            score.line_level_score * Decimal(str(self.config.MATCH_WEIGHT_LINE_LEVEL)) +
            score.amount_score * Decimal(str(self.config.MATCH_WEIGHT_AMOUNT)) +
            score.date_score * Decimal(str(self.config.MATCH_WEIGHT_DATE))
        )
        
        return score

    def _calculate_line_score(
        self,
        po_line: PurchaseOrderLine,
        invoice_line: InvoiceLine
    ) -> Decimal:
        """Calculate score for a single line match."""
        score = Decimal("1.0")
        
        # Quantity match (50% of line score)
        qty_score = self._calculate_quantity_score(
            po_line.quantity,
            invoice_line.quantity
        )
        
        # Price match (50% of line score)
        price_score = self._calculate_price_score(
            po_line.unit_price,
            invoice_line.unit_price
        )
        
        score = (qty_score + price_score) / Decimal("2")
        
        return score

    def _calculate_quantity_score(
        self,
        po_quantity: Decimal,
        inv_quantity: Decimal
    ) -> Decimal:
        """Calculate quantity match score."""
        if po_quantity == 0 and inv_quantity == 0:
            return Decimal("1.0")
        if po_quantity == 0 or inv_quantity == 0:
            return Decimal("0.0")
        
        ratio = min(po_quantity, inv_quantity) / max(po_quantity, inv_quantity)
        return max(Decimal("0"), min(Decimal("1.0"), ratio))

    def _calculate_price_score(
        self,
        po_price: Decimal,
        inv_price: Decimal
    ) -> Decimal:
        """Calculate price match score."""
        if po_price == 0 and inv_price == 0:
            return Decimal("1.0")
        if po_price == 0 or inv_price == 0:
            return Decimal("0.0")
        
        # Allow small tolerance (1%)
        tolerance = Decimal("0.01")
        if abs(po_price - inv_price) / po_price <= tolerance:
            return Decimal("1.0")
        
        ratio = min(po_price, inv_price) / max(po_price, inv_price)
        return max(Decimal("0"), min(Decimal("1.0"), ratio))

    def _calculate_amount_score(
        self,
        invoice_amount: Decimal,
        po_amount: Decimal,
        matched_amounts: list[Decimal]
    ) -> Decimal:
        """Calculate amount match score."""
        if po_amount == 0 and invoice_amount == 0:
            return Decimal("1.0")
        if po_amount == 0 or invoice_amount == 0:
            return Decimal("0.0")
        
        total_matched = sum(matched_amounts)
        
        # Check if fully matched
        if abs(total_matched - invoice_amount) <= self.AMOUNT_TOLERANCE:
            if abs(invoice_amount - po_amount) <= self.AMOUNT_TOLERANCE:
                return Decimal("1.0")
            elif invoice_amount < po_amount:
                # Partial match - check percentage
                return invoice_amount / po_amount
        
        # Calculate variance penalty
        variance = abs(invoice_amount - po_amount)
        variance_ratio = 1 - (variance / po_amount)
        return max(Decimal("0"), min(Decimal("1.0"), variance_ratio))

    def _calculate_date_score(
        self,
        doc_date: date,
        po_date: date
    ) -> Decimal:
        """Calculate date match score."""
        days_diff = abs((doc_date - po_date).days)
        
        if days_diff == 0:
            return Decimal("1.0")
        elif days_diff <= self.DATE_TOLERANCE_DAYS:
            return Decimal("1.0") - Decimal(str(days_diff / 30))
        else:
            # Exponential decay for large differences
            return max(Decimal("0"), Decimal("1.0") - Decimal(str(days_diff / 365)))

    def _calculate_variances(
        self,
        score: MatchScore,
        invoice: Invoice,
        purchase_order: PurchaseOrder
    ) -> dict:
        """Calculate variance details."""
        qty_variance = sum(ls.quantity_variance for ls in score.line_matches)
        price_variance = sum(ls.price_variance for ls in score.line_matches)
        date_variance = (invoice.invoice_date - purchase_order.order_date).days
        
        return {
            "quantity": qty_variance,
            "price": price_variance,
            "date_days": date_variance
        }

    def _get_avg_unit_price(self, po: PurchaseOrder) -> Decimal:
        """Get average unit price from PO."""
        if not po.lines:
            return Decimal("0")
        total = sum(line.unit_price for line in po.lines)
        return total / Decimal(str(len(po.lines)))

    def _route_decision(self, total_score: Decimal) -> MatchStatus:
        """Route match to appropriate decision based on score."""
        if total_score >= Decimal(str(self.config.MATCH_THRESHOLD_AUTO_APPROVE)):
            return MatchStatus.AUTO_APPROVED
        elif total_score >= Decimal(str(self.config.MATCH_THRESHOLD_PENDING)):
            return MatchStatus.HUMAN_REVIEW
        else:
            return MatchStatus.REJECTED

    async def decide_match(
        self,
        match_id: UUID,
        decision: MatchDecision,
        resolved_by: Optional[UUID] = None
    ) -> Optional[Match]:
        """Process a human decision on a match."""
        result = await self.db.execute(
            select(Match).where(Match.id == match_id)
        )
        match = result.scalar_one_or_none()
        
        if not match:
            return None
        
        if decision.decision == MatchStatus.CONFIRMED:
            match.approve(resolved_by=resolved_by, notes=decision.notes)
        elif decision.decision == MatchStatus.REJECTED:
            match.reject(reason=decision.notes or "Rejected by user", resolved_by=resolved_by)
        else:
            match.status = decision.decision
            match.resolution_notes = decision.notes
        
        await self.db.flush()
        return match

    async def find_matching_po(
        self,
        invoice: Invoice,
        supplier_id: Optional[str] = None
    ) -> Optional[PurchaseOrder]:
        """Layer 1: Find potential matching PO for an invoice."""
        query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.is_deleted == False,
                PurchaseOrder.status == "OPEN"
            )
        )
        
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
        elif invoice.supplier_id:
            query = query.where(PurchaseOrder.supplier_id == invoice.supplier_id)
        
        # Order by most recent first
        query = query.order_by(PurchaseOrder.order_date.desc())
        
        result = await self.db.execute(query)
        pos = result.scalars().all()
        
        # Find best matching PO
        for po in pos:
            if po.supplier_id == invoice.supplier_id:
                return po
        
        return None

    async def find_matching_dn(
        self,
        invoice: Invoice,
        purchase_order_id: Optional[UUID] = None
    ) -> list[DeliveryNote]:
        """Find potential matching delivery notes for an invoice."""
        query = select(DeliveryNote).where(
            and_(
                DeliveryNote.is_deleted == False,
                DeliveryNote.status == "RECEIVED"
            )
        )
        
        if purchase_order_id:
            query = query.where(DeliveryNote.purchase_order_id == purchase_order_id)
        elif invoice.supplier_id:
            query = query.where(DeliveryNote.supplier_id == invoice.supplier_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
