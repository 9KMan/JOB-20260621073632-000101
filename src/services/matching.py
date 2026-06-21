// src/services/matching.py
"""3-Way Matching Engine Service."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.config import get_settings
from src.models.balance import Balance, BalanceType
from src.models.document import Document, DocumentType, DocumentStatus
from src.models.document_line import DocumentLine
from src.models.match import Match, MatchDecision, MatchLine, MatchStatus, MatchType
from src.services.balance import BalanceService

settings = get_settings()


class MatchingService:
    """
    3-Way Matching Engine Service.
    
    Architecture:
    - Layer 1: PO Anchoring - PO as single source of truth
    - Layer 2: Cascade Matching - Invoice↔PO, DN↔PO, Invoice↔DN
    - Layer 3: Balance Resolution - partial matches and multi-delivery
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.balance_service = BalanceService(db)
    
    # ==================== Layer 1: PO Anchoring ====================
    
    async def anchor_to_po(
        self,
        document: Document,
        supplier_code: Optional[str] = None,
        po_reference: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Layer 1: Anchor a document to its Purchase Order.
        Uses PO as single source of truth for matching.
        """
        # Try to find matching PO
        conditions = [Document.document_type == DocumentType.PURCHASE_ORDER]
        
        if po_reference:
            conditions.append(Document.document_number == po_reference)
        if supplier_code:
            conditions.append(Document.supplier_code == supplier_code)
        else:
            conditions.append(Document.supplier_code == document.supplier_code)
        
        # Look for open POs
        conditions.append(
            Document.status.in_([
                DocumentStatus.SUBMITTED,
                DocumentStatus.PARTIALLY_MATCHED,
            ])
        )
        
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.lines))
            .where(and_(*conditions))
            .order_by(Document.document_date.desc())
            .limit(1)
        )
        
        return result.scalar_one_or_none()
    
    # ==================== Layer 2: Cascade Matching ====================
    
    async def match_invoice_to_po(
        self,
        invoice: Document,
        po: Document,
    ) -> tuple[Decimal, Decimal, Decimal, list[dict]]:
        """
        Match invoice lines to PO lines.
        Returns: (line_score, amount_score, date_score, matched_lines)
        """
        line_score = Decimal("0")
        matched_lines = []
        total_matched_amount = Decimal("0")
        total_invoice_amount = invoice.total_amount
        total_po_amount = po.total_amount
        
        # Match line by line
        invoice_lines = {line.sku: line for line in invoice.lines if line.sku}
        
        for po_line in po.lines:
            matched_invoice_line = invoice_lines.get(po_line.sku)
            
            if matched_invoice_line:
                # Calculate quantity match
                qty_ratio = min(
                    matched_invoice_line.quantity / po_line.quantity
                    if po_line.quantity > 0 else Decimal("0"),
                    Decimal("1"),
                )
                
                # Calculate amount match
                expected_amount = po_line.line_total
                actual_amount = matched_invoice_line.line_total
                amount_ratio = Decimal("1") - min(
                    abs(expected_amount - actual_amount) / expected_amount
                    if expected_amount > 0 else Decimal("0"),
                    Decimal("1"),
                )
                
                line_score += qty_ratio * amount_ratio
                total_matched_amount += min(actual_amount, expected_amount)
                
                matched_lines.append({
                    "po_line_id": po_line.id,
                    "invoice_line_id": matched_invoice_line.id,
                    "matched_quantity": min(matched_invoice_line.quantity, po_line.quantity),
                    "matched_amount": min(actual_amount, expected_amount),
                })
        
        # Normalize scores
        max_lines = max(len(po.lines), 1)
        line_score = line_score / Decimal(max_lines)
        
        # Amount score
        if total_po_amount > 0:
            amount_score = Decimal("1") - min(
                abs(total_po_amount - total_invoice_amount) / total_po_amount,
                Decimal("1"),
            )
        else:
            amount_score = Decimal("0")
        
        # Date score
        date_score = self._calculate_date_score(
            invoice.document_date,
            po.document_date,
        )
        
        return line_score, amount_score, date_score, matched_lines
    
    async def match_delivery_to_po(
        self,
        delivery: Document,
        po: Document,
    ) -> tuple[Decimal, Decimal, Decimal, list[dict]]:
        """
        Match delivery note lines to PO lines.
        Returns: (line_score, amount_score, date_score, matched_lines)
        """
        line_score = Decimal("0")
        matched_lines = []
        total_delivered_amount = Decimal("0")
        total_po_amount = po.total_amount
        
        po_lines = {line.sku: line for line in po.lines if line.sku}
        
        for dn_line in delivery.lines:
            matched_po_line = po_lines.get(dn_line.sku)
            
            if matched_po_line:
                # Calculate quantity match using delivered quantity
                delivered_qty = dn_line.delivered_quantity or dn_line.quantity
                qty_ratio = min(
                    delivered_qty / matched_po_line.quantity
                    if matched_po_line.quantity > 0 else Decimal("0"),
                    Decimal("1"),
                )
                
                # Amount ratio
                expected_amount = matched_po_line.line_total
                actual_amount = dn_line.line_total
                amount_ratio = Decimal("1") - min(
                    abs(expected_amount - actual_amount) / expected_amount
                    if expected_amount > 0 else Decimal("0"),
                    Decimal("1"),
                )
                
                line_score += qty_ratio * amount_ratio
                total_delivered_amount += min(actual_amount, expected_amount)
                
                matched_lines.append({
                    "po_line_id": matched_po_line.id,
                    "dn_line_id": dn_line.id,
                    "matched_quantity": min(delivered_qty, matched_po_line.quantity),
                    "matched_amount": min(actual_amount, expected_amount),
                })
        
        # Normalize scores
        max_lines = max(len(po.lines), 1)
        line_score = line_score / Decimal(max_lines)
        
        # Amount score
        if total_po_amount > 0:
            amount_score = Decimal("1") - min(
                abs(total_po_amount - total_delivered_amount) / total_po_amount,
                Decimal("1"),
            )
        else:
            amount_score = Decimal("0")
        
        # Date score (delivery date vs expected)
        expected_date = po.expected_delivery_date or po.document_date
        date_score = self._calculate_date_score(
            delivery.delivery_date or delivery.document_date,
            expected_date,
        )
        
        return line_score, amount_score, date_score, matched_lines
    
    async def match_invoice_to_delivery(
        self,
        invoice: Document,
        delivery: Document,
    ) -> tuple[Decimal, Decimal, Decimal, list[dict]]:
        """
        Match invoice lines to delivery note lines.
        Returns: (line_score, amount_score, date_score, matched_lines)
        """
        line_score = Decimal("0")
        matched_lines = []
        total_invoice_amount = invoice.total_amount
        total_delivery_amount = delivery.total_amount
        
        invoice_lines = {line.sku: line for line in invoice.lines if line.sku}
        delivery_lines = {line.sku: line for line in delivery.lines if line.sku}
        
        for sku, inv_line in invoice_lines.items():
            if sku in delivery_lines:
                dn_line = delivery_lines[sku]
                
                # Quantity match
                delivered_qty = dn_line.delivered_quantity or dn_line.quantity
                qty_ratio = min(
                    inv_line.quantity / delivered_qty
                    if delivered_qty > 0 else Decimal("0"),
                    Decimal("1"),
                )
                
                # Amount match
                amount_ratio = Decimal("1") - min(
                    abs(inv_line.line_total - dn_line.line_total) / dn_line.line_total
                    if dn_line.line_total > 0 else Decimal("0"),
                    Decimal("1"),
                )
                
                line_score += qty_ratio * amount_ratio
                
                matched_lines.append({
                    "invoice_line_id": inv_line.id,
                    "dn_line_id": dn_line.id,
                    "matched_quantity": inv_line.quantity,
                    "matched_amount": inv_line.line_total,
                })
        
        # Normalize
        max_lines = max(len(invoice.lines), len(delivery.lines), 1)
        line_score = line_score / Decimal(max_lines)
        
        # Amount score
        if total_delivery_amount > 0:
            amount_score = Decimal("1") - min(
                abs(total_delivery_amount - total_invoice_amount) / total_delivery_amount,
                Decimal("1"),
            )
        else:
            amount_score = Decimal("0")
        
        # Date score
        date_score = self._calculate_date_score(
            invoice.document_date,
            delivery.delivery_date or delivery.document_date,
        )
        
        return line_score, amount_score, date_score, matched_lines
    
    def _calculate_date_score(
        self,
        date1: date,
        date2: date,
    ) -> Decimal:
        """Calculate date similarity score (0-1)."""
        days_diff = abs((date1 - date2).days)
        tolerance = settings.DATE_TOLERANCE_DAYS
        
        if days_diff <= tolerance:
            return Decimal("1")
        elif days_diff <= tolerance * 2:
            return Decimal("0.5")
        else:
            return Decimal("0")
    
    def _calculate_total_score(
        self,
        line_score: Decimal,
        amount_score: Decimal,
        date_score: Decimal,
    ) -> Decimal:
        """Calculate weighted total match score."""
        return (
            line_score * Decimal(str(settings.MATCHING_LINE_WEIGHT)) +
            amount_score * Decimal(str(settings.MATCHING_AMOUNT_WEIGHT)) +
            date_score * Decimal(str(settings.MATCHING_DATE_WEIGHT))
        )
    
    # ==================== Layer 3: Balance Resolution ====================
    
    async def resolve_balance(
        self,
        source_document: Document,
        target_document: Document,
        matched_amount: Decimal,
    ) -> dict:
        """
        Layer 3: Resolve balances between matched documents.
        Handles partial matches and multi-delivery scenarios.
        """
        # Get or create balances
        source_balance = await self.balance_service.get_or_create_balance(
            source_document.id,
            BalanceType.DEBIT if source_document.is_po or source_document.is_delivery_note
            else BalanceType.CREDIT,
            source_document.total_amount,
        )
        
        target_balance = await self.balance_service.get_or_create_balance(
            target_document.id,
            BalanceType.CREDIT if target_document.is_po or target_document.is_delivery_note
            else BalanceType.DEBIT,
            target_document.total_amount,
        )
        
        # Update matched amounts
        source_balance.matched_amount += matched_amount
        target_balance.matched_amount += matched_amount
        
        source_balance.reference_document_id = target_document.id
        source_balance.reference_document_number = target_document.document_number
        target_balance.reference_document_id = source_document.id
        target_balance.reference_document_number = source_document.document_number
        
        await self.db.flush()
        
        return {
            "source_open_amount": source_balance.open_amount,
            "target_open_amount": target_balance.open_amount,
            "source_fully_matched": source_balance.is_fully_matched,
            "target_fully_matched": target_balance.is_fully_matched,
        }
    
    # ==================== Decision Routing ====================
    
    def route_decision(self, total_score: Decimal) -> MatchDecision:
        """
        Route match to appropriate decision path.
        - CONFIRMED + HIGH_SCORE → AUTO_APPROVED
        - PENDING + MEDIUM_SCORE → HUMAN_REVIEW
        - LOW_SCORE → DISPUTED
        """
        if total_score >= Decimal(str(settings.AUTO_APPROVE_THRESHOLD)):
            return MatchDecision.AUTO_APPROVED
        elif total_score >= Decimal(str(settings.HUMAN_REVIEW_THRESHOLD)):
            return MatchDecision.HUMAN_REVIEW
        else:
            return MatchDecision.DISPUTED
    
    # ==================== Main Matching Interface ====================
    
    async def find_matches_for_document(
        self,
        document_id: str,
        match_type: Optional[MatchType] = None,
    ) -> list[Match]:
        """Find existing matches for a document."""
        query = select(Match).where(
            or_(
                Match.source_document_id == document_id,
                Match.target_document_id == document_id,
                Match.third_document_id == document_id,
            )
        ).options(
            selectinload(Match.lines),
            selectinload(Match.source_document),
            selectinload(Match.target_document),
        )
        
        if match_type:
            query = query.where(Match.match_type == match_type)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_match(
        self,
        source_document_id: str,
        target_document_id: str,
        match_type: MatchType,
        line_score: Decimal,
        amount_score: Decimal,
        date_score: Decimal,
        matched_lines: list[dict],
        matched_amount: Decimal,
        variance_amount: Decimal,
        third_document_id: Optional[str] = None,
    ) -> Match:
        """Create a new match record."""
        total_score = self._calculate_total_score(line_score, amount_score, date_score)
        decision = self.route_decision(total_score)
        
        # Determine status based on decision
        status = MatchStatus.CONFIRMED if decision == MatchDecision.AUTO_APPROVED else MatchStatus.PENDING
        
        match = Match(
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            third_document_id=third_document_id,
            match_type=match_type,
            total_score=total_score,
            line_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            matched_amount=matched_amount,
            variance_amount=variance_amount,
            status=status,
            decision=decision,
        )
        
        self.db.add(match)
        await self.db.flush()
        
        # Create match lines
        for line_data in matched_lines:
            match_line = MatchLine(
                match_id=match.id,
                source_line_id=line_data.get("po_line_id") or line_data.get("invoice_line_id"),
                target_line_id=line_data.get("invoice_line_id") or line_data.get("dn_line_id"),
                matched_quantity=line_data.get("matched_quantity", Decimal("0")),
                variance_quantity=line_data.get("variance_quantity", Decimal("0")),
                matched_amount=line_data.get("matched_amount", Decimal("0")),
                variance_amount=line_data.get("variance_amount", Decimal("0")),
                score=line_score,
            )
            self.db.add(match_line)
        
        await self.db.flush()
        await self.db.refresh(match)
        
        return match
    
    async def full_three_way_match(
        self,
        invoice_id: str,
        delivery_id: str,
        po_id: str,
    ) -> Match:
        """
        Perform complete 3-way match between Invoice, Delivery Note, and PO.
        """
        # Load documents
        invoice = await self.db.get(Document, invoice_id, options=[selectinload(Document.lines)])
        delivery = await self.db.get(Document, delivery_id, options=[selectinload(Document.lines)])
        po = await self.db.get(Document, po_id, options=[selectinload(Document.lines)])
        
        if not all([invoice, delivery, po]):
            raise ValueError("One or more documents not found")
        
        # Calculate individual match scores
        inv_po_scores = await self.match_invoice_to_po(invoice, po)
        dn_po_scores = await self.match_delivery_to_po(delivery, po)
        inv_dn_scores = await self.match_invoice_to_delivery(invoice, delivery)
        
        # Average the scores for 3-way match
        line_score = (inv_po_scores[0] + dn_po_scores[0] + inv_dn_scores[0]) / Decimal("3")
        amount_score = (inv_po_scores[1] + dn_po_scores[1] + inv_dn_scores[1]) / Decimal("3")
        date_score = (inv_po_scores[2] + dn_po_scores[2] + inv_dn_scores[2]) / Decimal("3")
        
        # Combined matched lines
        all_matched_lines = inv_po_scores[3] + dn_po_scores[3] + inv_dn_scores[3]
        
        # Matched amount (minimum of all three documents)
        matched_amount = min(invoice.total_amount, delivery.total_amount, po.total_amount)
        variance_amount = abs(invoice.total_amount - po.total_amount)
        
        # Create 3-way match
        match = await self.create_match(
            source_document_id=invoice_id,
            target_document_id=delivery_id,
            match_type=MatchType.THREE_WAY,
            line_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            matched_lines=all_matched_lines,
            matched_amount=matched_amount,
            variance_amount=variance_amount,
            third_document_id=po_id,
        )
        
        # Resolve balances
        await self.resolve_balance(invoice, po, matched_amount)
        await self.resolve_balance(delivery, po, matched_amount)
        await self.resolve_balance(invoice, delivery, matched_amount)
        
        return match
