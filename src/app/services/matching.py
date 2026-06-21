// src/app/services/matching.py
"""3-Way Matching service implementing the core matching engine."""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from dataclasses import dataclass

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine, PO_STATUS
from app.models.invoice import Invoice, InvoiceLine, INVOICE_STATUS
from app.models.delivery_note import DeliveryNote, DeliveryNoteLine, DN_STATUS
from app.models.match import Match, MatchLine, MatchDecision, MatchType, BalanceLedger
from app.schemas.match import MatchScoreSummary


@dataclass
class LineScore:
    """Score for a single line match."""
    product_score: Decimal
    quantity_score: Decimal
    price_score: Decimal
    total_score: Decimal
    quantity_variance: Decimal
    amount_variance: Decimal


@dataclass
class MatchResult:
    """Result of a match operation."""
    match_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    variance_amount: Decimal
    line_scores: List[LineScore]
    match_type: MatchType


class MatchingService:
    """Service for 3-way matching operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.weights = {
            "line_level": Decimal(str(settings.MATCH_WEIGHT_LINE_LEVEL)),
            "amount": Decimal(str(settings.MATCH_WEIGHT_AMOUNT)),
            "date": Decimal(str(settings.MATCH_WEIGHT_DATE)),
        }

    async def find_po_by_reference(
        self,
        supplier_id: str,
        po_reference: str,
    ) -> Optional[PurchaseOrder]:
        """Find a PO by reference for anchoring (Layer 1)."""
        stmt = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.po_number == po_reference,
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_([
                    PO_STATUS.SENT,
                    PO_STATUS.CONFIRMED,
                    PO_STATUS.PARTIAL,
                ]),
            )
        ).options(selectinload(PurchaseOrder.lines))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_open_pos_by_supplier(
        self,
        supplier_id: str,
    ) -> List[PurchaseOrder]:
        """Find all open POs for a supplier."""
        stmt = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_([
                    PO_STATUS.SENT,
                    PO_STATUS.CONFIRMED,
                    PO_STATUS.PARTIAL,
                ]),
            )
        ).options(selectinload(PurchaseOrder.lines))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_invoice_by_number(
        self,
        invoice_number: str,
    ) -> Optional[Invoice]:
        """Find an invoice by number."""
        stmt = select(Invoice).where(
            Invoice.invoice_number == invoice_number
        ).options(selectinload(Invoice.lines))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_invoices_by_po(
        self,
        po_id: uuid.UUID,
    ) -> List[Invoice]:
        """Find all invoices for a PO."""
        stmt = select(Invoice).where(
            Invoice.po_reference == str(po_id)
        ).options(selectinload(Invoice.lines))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_delivery_note_by_number(
        self,
        dn_number: str,
    ) -> Optional[DeliveryNote]:
        """Find a delivery note by number."""
        stmt = select(DeliveryNote).where(
            DeliveryNote.dn_number == dn_number
        ).options(selectinload(DeliveryNote.lines))

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_delivery_notes_by_po(
        self,
        po_id: uuid.UUID,
    ) -> List[DeliveryNote]:
        """Find all delivery notes for a PO."""
        stmt = select(DeliveryNote).where(
            DeliveryNote.po_reference == str(po_id)
        ).options(selectinload(DeliveryNote.lines))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _calculate_line_score(
        self,
        po_line: Optional[PurchaseOrderLine],
        invoice_line: Optional[InvoiceLine],
        dn_line: Optional[DeliveryNoteLine],
    ) -> LineScore:
        """Calculate matching score for a single line."""
        # Product/description matching
        product_score = Decimal("0.0000")
        if po_line and invoice_line:
            if po_line.product_code == invoice_line.product_code:
                product_score = Decimal("1.0000")
            elif (
                po_line.product_description.lower() in invoice_line.product_description.lower()
                or invoice_line.product_description.lower() in po_line.product_description.lower()
            ):
                product_score = Decimal("0.7500")

        # Quantity matching
        quantity_score = Decimal("0.0000")
        quantity_variance = Decimal("0.0000")
        invoice_qty = invoice_line.quantity if invoice_line else Decimal("0")
        po_qty = po_line.quantity if po_line else Decimal("0")
        dn_qty = dn_line.quantity_delivered if dn_line else Decimal("0")

        if po_qty > 0:
            # For 3-way matching, consider DN quantity
            reference_qty = dn_qty if dn_qty > 0 else po_qty
            if reference_qty > 0:
                if invoice_qty == reference_qty:
                    quantity_score = Decimal("1.0000")
                else:
                    min_qty = min(invoice_qty, reference_qty)
                    max_qty = max(invoice_qty, reference_qty)
                    quantity_score = min_qty / max_qty
                quantity_variance = abs(invoice_qty - reference_qty)

        # Price matching
        price_score = Decimal("0.0000")
        po_price = po_line.unit_price if po_line else Decimal("0")
        invoice_price = invoice_line.unit_price if invoice_line else Decimal("0")

        if po_price > 0:
            if invoice_price == po_price:
                price_score = Decimal("1.0000")
            else:
                min_price = min(invoice_price, po_price)
                max_price = max(invoice_price, po_price)
                price_score = min_price / max_price

        # Line total
        invoice_total = invoice_line.line_total if invoice_line else Decimal("0")
        po_total = po_line.line_total if po_line else Decimal("0")
        dn_total = dn_line.quantity_delivered * po_price if dn_line and po_line else Decimal("0")

        line_total = (product_score + quantity_score + price_score) / Decimal("3")
        amount_variance = abs(invoice_total - po_total)

        return LineScore(
            product_score=product_score,
            quantity_score=quantity_score,
            price_score=price_score,
            total_score=line_total,
            quantity_variance=quantity_variance,
            amount_variance=amount_variance,
        )

    async def match_invoice_to_po(
        self,
        invoice: Invoice,
        po: PurchaseOrder,
    ) -> MatchResult:
        """Match invoice lines to PO lines (Layer 2 - Cascade)."""
        line_scores: List[LineScore] = []
        matched_lines = 0

        for inv_line in invoice.lines:
            best_score = LineScore(
                product_score=Decimal("0"),
                quantity_score=Decimal("0"),
                price_score=Decimal("0"),
                total_score=Decimal("0"),
                quantity_variance=Decimal("0"),
                amount_variance=Decimal("0"),
            )

            for po_line in po.lines:
                score = self._calculate_line_score(po_line, inv_line, None)
                if score.total_score > best_score.total_score:
                    best_score = score

            line_scores.append(best_score)
            if best_score.total_score >= Decimal("0.7"):
                matched_lines += 1

        # Calculate aggregate scores
        total_lines = len(invoice.lines) if invoice.lines else 1
        line_level_score = sum(ls.total_score for ls in line_scores) / Decimal(total_lines)

        # Amount score
        po_amount = po.total_amount
        invoice_amount = invoice.total_amount
        if po_amount > 0:
            amount_score = min(invoice_amount, po_amount) / max(invoice_amount, po_amount)
        else:
            amount_score = Decimal("1.0000") if invoice_amount == 0 else Decimal("0.0000")

        variance_amount = abs(invoice_amount - po_amount)

        # Date score (based on invoice date vs PO date)
        date_diff = abs((invoice.invoice_date - po.order_date).days)
        date_score = max(Decimal("0"), Decimal("1") - Decimal(str(date_diff / 365)))

        # Total match score
        match_score = (
            line_level_score * self.weights["line_level"]
            + amount_score * self.weights["amount"]
            + date_score * self.weights["date"]
        )

        return MatchResult(
            match_score=match_score,
            line_level_score=line_level_score,
            amount_score=amount_score,
            date_score=date_score,
            variance_amount=variance_amount,
            line_scores=line_scores,
            match_type=MatchType.INVOICE_PO,
        )

    async def match_dn_to_po(
        self,
        dn: DeliveryNote,
        po: PurchaseOrder,
    ) -> MatchResult:
        """Match delivery note lines to PO lines (Layer 2 - Cascade)."""
        line_scores: List[LineScore] = []
        matched_lines = 0

        for dn_line in dn.lines:
            best_score = LineScore(
                product_score=Decimal("0"),
                quantity_score=Decimal("0"),
                price_score=Decimal("0"),
                total_score=Decimal("0"),
                quantity_variance=Decimal("0"),
                amount_variance=Decimal("0"),
            )

            for po_line in po.lines:
                if po_line.product_code == dn_line.product_code:
                    score = self._calculate_line_score(po_line, None, dn_line)
                    if score.total_score > best_score.total_score:
                        best_score = score

            line_scores.append(best_score)
            if best_score.total_score >= Decimal("0.7"):
                matched_lines += 1

        total_lines = len(dn.lines) if dn.lines else 1
        line_level_score = sum(ls.total_score for ls in line_scores) / Decimal(total_lines)

        po_amount = po.total_amount
        dn_amount = dn.total_amount
        if po_amount > 0:
            amount_score = min(dn_amount, po_amount) / max(dn_amount, po_amount)
        else:
            amount_score = Decimal("1.0000")

        variance_amount = abs(dn_amount - po_amount)

        # Date score
        date_diff = abs((dn.delivery_date - po.order_date).days)
        date_score = max(Decimal("0"), Decimal("1") - Decimal(str(date_diff / 365)))

        match_score = (
            line_level_score * self.weights["line_level"]
            + amount_score * self.weights["amount"]
            + date_score * self.weights["date"]
        )

        return MatchResult(
            match_score=match_score,
            line_level_score=line_level_score,
            amount_score=amount_score,
            date_score=date_score,
            variance_amount=variance_amount,
            line_scores=line_scores,
            match_type=MatchType.DN_PO,
        )

    async def match_invoice_to_dn(
        self,
        invoice: Invoice,
        dn: DeliveryNote,
    ) -> MatchResult:
        """Match invoice lines to delivery note lines (Layer 2 - Cascade)."""
        line_scores: List[LineScore] = []
        matched_lines = 0

        for inv_line in invoice.lines:
            best_score = LineScore(
                product_score=Decimal("0"),
                quantity_score=Decimal("0"),
                price_score=Decimal("0"),
                total_score=Decimal("0"),
                quantity_variance=Decimal("0"),
                amount_variance=Decimal("0"),
            )

            for dn_line in dn.lines:
                if inv_line.product_code == dn_line.product_code:
                    # Create pseudo PO line for scoring
                    po_line = PurchaseOrderLine(
                        product_code=dn_line.product_code,
                        product_description=dn_line.product_description,
                        quantity=dn_line.quantity_delivered,
                        unit_price=inv_line.unit_price,
                        line_total=dn_line.quantity_delivered * inv_line.unit_price,
                    )
                    score = self._calculate_line_score(po_line, inv_line, dn_line)
                    if score.total_score > best_score.total_score:
                        best_score = score

            line_scores.append(best_score)
            if best_score.total_score >= Decimal("0.7"):
                matched_lines += 1

        total_lines = len(invoice.lines) if invoice.lines else 1
        line_level_score = sum(ls.total_score for ls in line_scores) / Decimal(total_lines)

        invoice_amount = invoice.total_amount
        dn_amount = dn.total_amount
        if dn_amount > 0:
            amount_score = min(invoice_amount, dn_amount) / max(invoice_amount, dn_amount)
        else:
            amount_score = Decimal("1.0000")

        variance_amount = abs(invoice_amount - dn_amount)

        # Date score
        date_diff = abs((invoice.invoice_date - dn.delivery_date).days)
        date_score = max(Decimal("0"), Decimal("1") - Decimal(str(date_diff / 365)))

        match_score = (
            line_level_score * self.weights["line_level"]
            + amount_score * self.weights["amount"]
            + date_score * self.weights["date"]
        )

        return MatchResult(
            match_score=match_score,
            line_level_score=line_level_score,
            amount_score=amount_score,
            date_score=date_score,
            variance_amount=variance_amount,
            line_scores=line_scores,
            match_type=MatchType.INVOICE_DN,
        )

    async def perform_three_way_match(
        self,
        invoice: Invoice,
        delivery_notes: List[DeliveryNote],
        po: PurchaseOrder,
    ) -> Tuple[MatchResult, List[MatchResult]]:
        """Perform complete 3-way matching."""
        # Match invoice to PO
        invoice_po_result = await self.match_invoice_to_po(invoice, po)

        # Match each DN to PO
        dn_results = []
        for dn in delivery_notes:
            dn_result = await self.match_dn_to_po(dn, po)
            dn_results.append(dn_result)

        # Create 3-way match result
        avg_line_score = invoice_po_result.line_level_score
        if dn_results:
            avg_line_score = sum(r.line_level_score for r in dn_results) / Decimal(len(dn_results))

        total_invoice = invoice.total_amount
        total_dn = sum(dn.total_amount for dn in delivery_notes)
        total_po = po.total_amount

        # Weighted amount score
        reference_amount = min(total_invoice, total_po, total_dn) if delivery_notes else min(total_invoice, total_po)
        max_amount = max(total_invoice, total_po, total_dn) if delivery_notes else max(total_invoice, total_po)
        amount_score = reference_amount / max_amount if max_amount > 0 else Decimal("1.0000")

        variance_amount = max(total_invoice, total_po, total_dn) - min(total_invoice, total_po, total_dn)

        # Calculate date score
        dates = [invoice.invoice_date, po.order_date]
        for dn in delivery_notes:
            dates.append(dn.delivery_date)
        date_range = (max(dates) - min(dates)).days
        date_score = max(Decimal("0"), Decimal("1") - Decimal(str(date_range / 365)))

        overall_score = (
            avg_line_score * self.weights["line_level"]
            + amount_score * self.weights["amount"]
            + date_score * self.weights["date"]
        )

        three_way_result = MatchResult(
            match_score=overall_score,
            line_level_score=avg_line_score,
            amount_score=amount_score,
            date_score=date_score,
            variance_amount=variance_amount,
            line_scores=invoice_po_result.line_scores,
            match_type=MatchType.THREE_WAY,
        )

        return three_way_result, dn_results

    def determine_decision(self, match_score: Decimal) -> MatchDecision:
        """Determine match decision based on score (Decision Routing)."""
        if match_score >= Decimal(str(settings.AUTO_APPROVE_THRESHOLD)):
            return MatchDecision.AUTO_APPROVED
        elif match_score >= Decimal(str(settings.HUMAN_REVIEW_THRESHOLD)):
            return MatchDecision.HUMAN_REVIEW
        else:
            return MatchDecision.REJECTED

    async def create_match(
        self,
        invoice: Invoice,
        po: Optional[PurchaseOrder],
        dn: Optional[DeliveryNote],
        result: MatchResult,
        decision: Optional[MatchDecision] = None,
    ) -> Match:
        """Create a match record from a match result."""
        if decision is None:
            decision = self.determine_decision(result.match_score)

        match = Match(
            purchase_order_id=po.id if po else None,
            invoice_id=invoice.id,
            delivery_note_id=dn.id if dn else None,
            match_type=result.match_type,
            match_score=result.match_score,
            line_level_score=result.line_level_score,
            amount_score=result.amount_score,
            date_score=result.date_score,
            po_amount=po.total_amount if po else Decimal("0.00"),
            invoice_amount=invoice.total_amount,
            dn_amount=dn.total_amount if dn else Decimal("0.00"),
            variance_amount=result.variance_amount,
            decision=decision,
        )

        self.db.add(match)
        await self.db.flush()

        # Create line matches
        for i, line_score in enumerate(result.line_scores):
            inv_line = invoice.lines[i] if i < len(invoice.lines) else None

            # Find best matching PO line
            po_line = None
            if po and inv_line:
                for pol in po.lines:
                    if pol.product_code == inv_line.product_code:
                        po_line = pol
                        break

            # Find best matching DN line
            dn_line = None
            if dn and inv_line:
                for dnl in dn.lines:
                    if dnl.product_code == inv_line.product_code:
                        dn_line = dnl
                        break

            match_line = MatchLine(
                match_id=match.id,
                po_line_id=po_line.id if po_line else None,
                invoice_line_id=inv_line.id if inv_line else None,
                dn_line_id=dn_line.id if dn_line else None,
                product_match_score=line_score.product_score,
                quantity_match_score=line_score.quantity_score,
                price_match_score=line_score.price_score,
                line_total_score=line_score.total_score,
                po_quantity=po_line.quantity if po_line else None,
                invoice_quantity=inv_line.quantity if inv_line else None,
                dn_quantity=dn_line.quantity_delivered if dn_line else None,
                quantity_variance=line_score.quantity_variance,
                po_line_total=po_line.line_total if po_line else None,
                invoice_line_total=inv_line.line_total if inv_line else None,
                dn_line_total=dn_line.quantity_delivered * (po_line.unit_price if po_line else inv_line.unit_price) if dn_line else None,
                amount_variance=line_score.amount_variance,
            )
            self.db.add(match_line)

        await self.db.flush()
        await self.db.refresh(match)
        return match

    async def confirm_match(
        self,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        decision: MatchDecision,
        notes: Optional[str] = None,
        dispute_reason: Optional[str] = None,
    ) -> Match:
        """Confirm/override a match decision."""
        stmt = select(Match).where(Match.id == match_id)
        result = await self.db.execute(stmt)
        match = result.scalar_one_or_none()

        if not match:
            raise ValueError(f"Match {match_id} not found")

        match.decision = decision
        match.confirmed_by_id = user_id
        match.confirmed_at = datetime.now(timezone.utc)
        if notes:
            match.notes = notes
        if dispute_reason:
            match.dispute_reason = dispute_reason

        await self.db.flush()
        await self.db.refresh(match)
        return match


class BalanceService:
    """Service for managing balance ledger (Layer 3)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(
        self,
        document_type: str,
        document_id: uuid.UUID,
        document_line_id: Optional[uuid.UUID] = None,
    ) -> Optional[BalanceLedger]:
        """Get current balance for a document."""
        conditions = [
            BalanceLedger.document_type == document_type,
            BalanceLedger.document_id == document_id,
        ]
        if document_line_id:
            conditions.append(BalanceLedger.document_line_id == document_line_id)

        stmt = select(BalanceLedger).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_balance(
        self,
        document_type: str,
        document_id: uuid.UUID,
        original_amount: Decimal,
        matched_amount: Decimal = Decimal("0"),
        document_line_id: Optional[uuid.UUID] = None,
        match_id: Optional[uuid.UUID] = None,
        currency: str = "USD",
    ) -> BalanceLedger:
        """Create or update a balance record."""
        existing = await self.get_balance(document_type, document_id, document_line_id)

        if existing:
            existing.matched_amount += matched_amount
            existing.remaining_balance = existing.original_amount - existing.matched_amount
            if match_id:
                existing.match_id = match_id
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            balance = BalanceLedger(
                document_type=document_type,
                document_id=document_id,
                document_line_id=document_line_id,
                original_amount=original_amount,
                matched_amount=matched_amount,
                remaining_balance=original_amount - matched_amount,
                match_id=match_id,
                currency=currency,
            )
            self.db.add(balance)
            await self.db.flush()
            await self.db.refresh(balance)
            return balance

    async def get_unmatched_balance(
        self,
        supplier_id: Optional[str] = None,
    ) -> List[BalanceLedger]:
        """Get all balances with remaining amount."""
        conditions = [BalanceLedger.remaining_balance > Decimal("0")]

        stmt = select(BalanceLedger).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def reconcile_balance(
        self,
        balance_id: uuid.UUID,
        match_id: uuid.UUID,
        amount: Decimal,
    ) -> BalanceLedger:
        """Reconcile a balance with a match."""
        stmt = select(BalanceLedger).where(BalanceLedger.id == balance_id)
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()

        if not balance:
            raise ValueError(f"Balance {balance_id} not found")

        balance.matched_amount += amount
        balance.remaining_balance = balance.original_amount - balance.matched_amount
        balance.match_id = match_id

        await self.db.flush()
        await self.db.refresh(balance)
        return balance
