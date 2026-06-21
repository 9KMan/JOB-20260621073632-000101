// src/services/matching_service.py
"""
3-Way Matching Engine Service

Layer 1: PO Anchoring - Match invoice/delivery against POs as single source of truth
Layer 2: Cascade Matching - Match invoice↔PO, DN↔PO, invoice↔DN with weighted scoring
Layer 3: Balance Resolution - Track partial matches using balance ledger
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.models import (
    PurchaseOrder, PurchaseOrderLine,
    Invoice, InvoiceLine,
    DeliveryNote, DeliveryNoteLine,
    MatchResult, MatchScore, MatchStatus, MatchDecision,
    BalanceLedger
)
from src.app.config import settings

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for 3-way matching operations."""

    def __init__(self, db: Session):
        self.db = db
        self.line_weight = settings.MATCHING_LINE_WEIGHT
        self.amount_weight = settings.MATCHING_AMOUNT_WEIGHT
        self.date_weight = settings.MATCHING_DATE_WEIGHT
        self.auto_approve_threshold = settings.AUTO_APPROVE_THRESHOLD
        self.human_review_threshold = settings.HUMAN_REVIEW_THRESHOLD

    # ==================== LAYER 1: PO ANCHORING ====================
    
    def find_anchor_po(self, vendor_id: UUID, po_number: Optional[str] = None) -> Optional[PurchaseOrder]:
        """
        Find the anchor Purchase Order for matching.
        Uses PO number if provided, otherwise finds open POs by vendor.
        """
        query = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.status == "OPEN",
                PurchaseOrder.is_deleted == False
            )
        )
        
        if po_number:
            po = query.filter(PurchaseOrder.po_number == po_number).first()
            if po:
                logger.info(f"Found anchor PO by number: {po_number}")
                return po
        
        # Return most recent open PO for vendor
        po = query.order_by(PurchaseOrder.order_date.desc()).first()
        if po:
            logger.info(f"Found anchor PO by vendor: {po.po_number}")
        return po

    def link_document_to_po(self, document_type: str, document_id: UUID, po_id: UUID) -> bool:
        """Link an invoice or delivery note to a purchase order."""
        try:
            if document_type == "INVOICE":
                self.db.query(Invoice).filter(Invoice.id == document_id).update(
                    {"purchase_order_id": po_id}
                )
            elif document_type == "DELIVERY_NOTE":
                self.db.query(DeliveryNote).filter(DeliveryNote.id == document_id).update(
                    {"purchase_order_id": po_id}
                )
            self.db.commit()
            logger.info(f"Linked {document_type} {document_id} to PO {po_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to link document to PO: {e}")
            return False

    # ==================== LAYER 2: CASCADE MATCHING ====================
    
    def calculate_line_score(
        self,
        doc_lines: List[Any],
        po_lines: List[PurchaseOrderLine]
    ) -> Tuple[float, List[Dict]]:
        """
        Calculate line-level match score using weighted criteria:
        - Item code match: 30%
        - Description similarity: 30%
        - Quantity match: 25%
        - Price match: 15%
        """
        scores = []
        total_score = 0.0
        matched_count = 0

        for doc_line in doc_lines:
            best_match = None
            best_score = 0.0

            for po_line in po_lines:
                score, details = self._calculate_line_pair_score(doc_line, po_line)
                if score > best_score:
                    best_score = score
                    best_match = (po_line, details)

            if best_match and best_score > 0.5:
                scores.append({
                    "doc_line_id": doc_line.id,
                    "po_line_id": best_match[0].id,
                    "score": best_score,
                    "details": best_match[1]
                })
                total_score += best_score
                matched_count += 1

        if matched_count == 0:
            return 0.0, scores
        
        return total_score / max(len(doc_lines), matched_count), scores

    def _calculate_line_pair_score(self, doc_line: Any, po_line: PurchaseOrderLine) -> Tuple[float, Dict]:
        """Calculate score between a document line and a PO line."""
        score = 0.0
        details = {}

        # Item code match (30%)
        if doc_line.item_code and po_line.item_code:
            if doc_line.item_code.upper() == po_line.item_code.upper():
                score += 0.30
                details["item_match"] = True
            elif doc_line.item_code.upper() in po_line.item_code.upper():
                score += 0.15
                details["item_partial"] = True

        # Description similarity (30%)
        doc_desc = doc_line.description.upper() if doc_line.description else ""
        po_desc = po_line.description.upper() if po_line.description else ""
        if doc_desc == po_desc:
            score += 0.30
            details["desc_match"] = True
        elif doc_desc in po_desc or po_desc in doc_desc:
            score += 0.15
            details["desc_partial"] = True
        else:
            # Simple word overlap check
            doc_words = set(doc_desc.split())
            po_words = set(po_desc.split())
            if doc_words and po_words:
                overlap = len(doc_words & po_words) / len(doc_words | po_words)
                score += overlap * 0.30
                details["desc_overlap"] = overlap

        # Quantity match (25%)
        doc_qty = Decimal(str(doc_line.quantity))
        po_qty = Decimal(str(po_line.quantity))
        if po_qty > 0:
            qty_ratio = min(doc_qty, po_qty) / max(doc_qty, po_qty)
            qty_score = qty_ratio * 0.25
            score += qty_score
            details["qty_ratio"] = float(qty_ratio)
            details["qty_diff"] = float(abs(doc_qty - po_qty))

        # Price match (15%)
        doc_price = Decimal(str(doc_line.unit_price))
        po_price = Decimal(str(po_line.unit_price))
        if po_price > 0:
            price_ratio = min(doc_price, po_price) / max(doc_price, po_price)
            price_score = price_ratio * 0.15
            score += price_score
            details["price_ratio"] = float(price_ratio)
            details["price_diff"] = float(abs(doc_price - po_price))

        return min(score, 1.0), details

    def calculate_amount_score(self, doc_amount: Decimal, po_amount: Decimal) -> float:
        """Calculate amount match score (20% weight)."""
        if po_amount <= 0:
            return 0.0
        ratio = min(float(doc_amount), float(po_amount)) / max(float(doc_amount), float(po_amount))
        return ratio

    def calculate_date_score(self, doc_date: datetime, po_date: datetime, window_days: int = 7) -> float:
        """Calculate date match score (10% weight)."""
        delta = abs((doc_date - po_date).days)
        if delta <= window_days:
            return 1.0 - (delta / (window_days + 1))
        return max(0.0, 1.0 - (delta - window_days) / 30)

    def calculate_total_score(self, line_score: float, amount_score: float, date_score: float) -> float:
        """Calculate weighted total match score."""
        return (
            line_score * self.line_weight +
            amount_score * self.amount_weight +
            date_score * self.date_weight
        )

    def determine_decision(self, total_score: float) -> MatchDecision:
        """Determine match decision based on total score."""
        if total_score >= self.auto_approve_threshold:
            return MatchDecision.AUTO_APPROVE
        elif total_score >= self.human_review_threshold:
            return MatchDecision.HUMAN_REVIEW
        else:
            return MatchDecision.DISPUTE

    def match_invoice_to_po(
        self,
        invoice: Invoice,
        po: PurchaseOrder
    ) -> MatchResult:
        """Match an invoice to a purchase order."""
        # Calculate scores
        line_score, line_scores = self.calculate_line_score(
            invoice.lines, po.lines
        )
        amount_score = self.calculate_amount_score(
            invoice.total_amount, po.total_amount
        )
        date_score = self.calculate_date_score(
            invoice.invoice_date, po.order_date
        )
        total_score = self.calculate_total_score(line_score, amount_score, date_score)
        decision = self.determine_decision(total_score)
        
        # Calculate differences
        amount_diff = invoice.total_amount - po.total_amount
        
        # Create match result
        match_result = MatchResult(
            invoice_id=invoice.id,
            delivery_note_id=None,
            purchase_order_id=po.id,
            match_type="INVOICE_PO",
            match_status=MatchStatus.CONFIRMED if decision == MatchDecision.AUTO_APPROVE else MatchStatus.PENDING,
            match_decision=decision,
            total_score=total_score,
            line_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            amount_difference=amount_diff,
            quantity_difference=Decimal("0")
        )
        
        self.db.add(match_result)
        self.db.flush()
        
        # Add line scores
        for ls in line_scores:
            score = MatchScore(
                match_result_id=match_result.id,
                invoice_line_id=ls.get("doc_line_id"),
                po_line_id=ls.get("po_line_id"),
                score=ls.get("score", 0),
                quantity_difference=Decimal(str(ls.get("details", {}).get("qty_diff", 0))),
                price_difference=Decimal(str(ls.get("details", {}).get("price_diff", 0)))
            )
            self.db.add(score)
        
        self.db.commit()
        self.db.refresh(match_result)
        
        logger.info(f"Created match result {match_result.id} with score {total_score:.2f}")
        return match_result

    def match_delivery_note_to_po(
        self,
        dn: DeliveryNote,
        po: PurchaseOrder
    ) -> MatchResult:
        """Match a delivery note to a purchase order."""
        # Calculate scores
        line_score, line_scores = self.calculate_line_score(
            dn.lines, po.lines
        )
        amount_score = self.calculate_amount_score(
            dn.total_amount, po.total_amount
        )
        date_score = self.calculate_date_score(
            dn.delivery_date, po.order_date
        )
        total_score = self.calculate_total_score(line_score, amount_score, date_score)
        decision = self.determine_decision(total_score)
        
        # Calculate differences
        amount_diff = dn.total_amount - po.total_amount
        
        # Create match result
        match_result = MatchResult(
            invoice_id=None,
            delivery_note_id=dn.id,
            purchase_order_id=po.id,
            match_type="DN_PO",
            match_status=MatchStatus.CONFIRMED if decision == MatchDecision.AUTO_APPROVE else MatchStatus.PENDING,
            match_decision=decision,
            total_score=total_score,
            line_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            amount_difference=amount_diff,
            quantity_difference=Decimal("0")
        )
        
        self.db.add(match_result)
        self.db.flush()
        
        # Add line scores
        for ls in line_scores:
            score = MatchScore(
                match_result_id=match_result.id,
                delivery_note_line_id=ls.get("doc_line_id"),
                po_line_id=ls.get("po_line_id"),
                score=ls.get("score", 0),
                quantity_difference=Decimal(str(ls.get("details", {}).get("qty_diff", 0))),
                price_difference=Decimal(str(ls.get("details", {}).get("price_diff", 0)))
            )
            self.db.add(score)
        
        self.db.commit()
        self.db.refresh(match_result)
        
        logger.info(f"Created DN match result {match_result.id} with score {total_score:.2f}")
        return match_result

    def match_invoice_to_delivery_note(
        self,
        invoice: Invoice,
        dn: DeliveryNote
    ) -> MatchResult:
        """Match an invoice to a delivery note."""
        # Calculate scores
        line_score, line_scores = self.calculate_line_score(
            invoice.lines, dn.lines
        )
        amount_score = self.calculate_amount_score(
            invoice.total_amount, dn.total_amount
        )
        date_score = self.calculate_date_score(
            invoice.invoice_date, dn.delivery_date
        )
        total_score = self.calculate_total_score(line_score, amount_score, date_score)
        decision = self.determine_decision(total_score)
        
        # Calculate differences
        amount_diff = invoice.total_amount - dn.total_amount
        
        # Create match result
        match_result = MatchResult(
            invoice_id=invoice.id,
            delivery_note_id=dn.id,
            purchase_order_id=invoice.purchase_order_id or dn.purchase_order_id,
            match_type="INVOICE_DN",
            match_status=MatchStatus.PENDING,
            match_decision=decision,
            total_score=total_score,
            line_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            amount_difference=amount_diff,
            quantity_difference=Decimal("0")
        )
        
        self.db.add(match_result)
        self.db.flush()
        
        # Add line scores
        for ls in line_scores:
            score = MatchScore(
                match_result_id=match_result.id,
                invoice_line_id=ls.get("doc_line_id"),
                delivery_note_line_id=ls.get("doc_line_id"),
                score=ls.get("score", 0),
                quantity_difference=Decimal(str(ls.get("details", {}).get("qty_diff", 0))),
                price_difference=Decimal(str(ls.get("details", {}).get("price_diff", 0)))
            )
            self.db.add(score)
        
        self.db.commit()
        self.db.refresh(match_result)
        
        logger.info(f"Created Invoice-DN match result {match_result.id} with score {total_score:.2f}")
        return match_result

    def perform_3_way_match(
        self,
        invoice: Invoice,
        dn: DeliveryNote,
        po: PurchaseOrder
    ) -> Dict[str, MatchResult]:
        """Perform complete 3-way match and return all match results."""
        results = {}
        
        # Match 1: Invoice to PO
        results["invoice_po"] = self.match_invoice_to_po(invoice, po)
        
        # Match 2: Delivery Note to PO
        results["dn_po"] = self.match_delivery_note_to_po(dn, po)
        
        # Match 3: Invoice to Delivery Note
        results["invoice_dn"] = self.match_invoice_to_delivery_note(invoice, dn)
        
        # Calculate overall 3-way match score
        overall_score = (
            results["invoice_po"].total_score +
            results["dn_po"].total_score +
            results["invoice_dn"].total_score
        ) / 3
        
        # Create combined 3-way match result
        three_way_result = MatchResult(
            invoice_id=invoice.id,
            delivery_note_id=dn.id,
            purchase_order_id=po.id,
            match_type="3_WAY",
            match_status=MatchStatus.CONFIRMED if overall_score >= self.auto_approve_threshold else MatchStatus.PENDING,
            match_decision=self.determine_decision(overall_score),
            total_score=overall_score,
            line_score=(results["invoice_po"].line_score + results["dn_po"].line_score) / 2,
            amount_score=(results["invoice_po"].amount_score + results["dn_po"].amount_score + results["invoice_dn"].amount_score) / 3,
            date_score=(results["invoice_po"].date_score + results["dn_po"].date_score + results["invoice_dn"].date_score) / 3,
            amount_difference=invoice.total_amount - dn.total_amount,
            quantity_difference=Decimal("0")
        )
        
        self.db.add(three_way_result)
        self.db.commit()
        self.db.refresh(three_way_result)
        
        results["3_way"] = three_way_result
        
        logger.info(f"Created 3-way match with overall score {overall_score:.2f}")
        return results

    # ==================== LAYER 3: BALANCE RESOLUTION ====================
    
    def initialize_po_balance(self, po: PurchaseOrder) -> List[BalanceLedger]:
        """Initialize balance ledger entries for a new PO."""
        balances = []
        
        for line in po.lines:
            balance = BalanceLedger(
                document_type="PO",
                document_id=po.id,
                document_line_id=line.id,
                balance_type="OPEN",
                amount=line.line_total,
                currency=po.currency,
                notes=f"PO {po.po_number} open quantity"
            )
            balances.append(balance)
            self.db.add(balance)
        
        self.db.commit()
        logger.info(f"Initialized balance ledger for PO {po.po_number}")
        return balances

    def record_invoice_balance(
        self,
        invoice: Invoice,
        po_id: Optional[UUID] = None
    ) -> BalanceLedger:
        """Record invoice in balance ledger."""
        balance = BalanceLedger(
            document_type="INVOICE",
            document_id=invoice.id,
            balance_type="INVOICED",
            amount=invoice.total_amount,
            related_document_type="PO" if po_id else None,
            related_document_id=po_id,
            currency=invoice.currency,
            notes=f"Invoice {invoice.invoice_number}"
        )
        
        self.db.add(balance)
        self.db.commit()
        
        logger.info(f"Recorded invoice balance for {invoice.invoice_number}")
        return balance

    def record_delivery_balance(
        self,
        dn: DeliveryNote,
        po_id: Optional[UUID] = None
    ) -> BalanceLedger:
        """Record delivery note in balance ledger."""
        balance = BalanceLedger(
            document_type="DN",
            document_id=dn.id,
            balance_type="DELIVERED",
            amount=dn.total_amount,
            related_document_type="PO" if po_id else None,
            related_document_id=po_id,
            currency=dn.currency,
            notes=f"Delivery Note {dn.dn_number}"
        )
        
        self.db.add(balance)
        self.db.commit()
        
        logger.info(f"Recorded delivery balance for {dn.dn_number}")
        return balance

    def calculate_po_balance(self, po_id: UUID) -> Dict[str, Decimal]:
        """Calculate current balance for a PO."""
        # Get PO total
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            return {"open": Decimal("0"), "invoiced": Decimal("0"), "delivered": Decimal("0"), "paid": Decimal("0")}
        
        po_total = Decimal(str(po.total_amount))
        
        # Calculate invoiced amount
        invoices = self.db.query(Invoice).filter(
            Invoice.purchase_order_id == po_id,
            Invoice.is_deleted == False
        ).all()
        invoiced_total = sum(Decimal(str(inv.total_amount)) for inv in invoices)
        
        # Calculate delivered amount
        dns = self.db.query(DeliveryNote).filter(
            DeliveryNote.purchase_order_id == po_id,
            DeliveryNote.is_deleted == False
        ).all()
        delivered_total = sum(Decimal(str(dn.total_amount)) for dn in dns)
        
        # Calculate paid amount
        paid_total = sum(
            Decimal(str(inv.amount_paid)) 
            for inv in invoices
        )
        
        return {
            "open": po_total - invoiced_total,
            "invoiced": invoiced_total,
            "delivered": delivered_total,
            "paid": paid_total,
            "po_total": po_total
        }

    def get_pending_matches(self, limit: int = 100) -> List[MatchResult]:
        """Get all pending match results for review."""
        return self.db.query(MatchResult).filter(
            MatchResult.match_status == MatchStatus.PENDING
        ).order_by(MatchResult.created_at.desc()).limit(limit).all()

    def approve_match(self, match_id: UUID, user_id: UUID, notes: Optional[str] = None) -> MatchResult:
        """Approve a pending match."""
        match = self.db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            raise ValueError(f"Match result {match_id} not found")
        
        match.match_status = MatchStatus.CONFIRMED
        match.match_decision = MatchDecision.AUTO_APPROVE
        match.decided_by = user_id
        match.decided_at = datetime.utcnow()
        if notes:
            match.notes = notes
        
        self.db.commit()
        self.db.refresh(match)
        
        logger.info(f"Approved match {match_id}")
        return match

    def reject_match(self, match_id: UUID, user_id: UUID, notes: Optional[str] = None) -> MatchResult:
        """Reject a pending match."""
        match = self.db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            raise ValueError(f"Match result {match_id} not found")
        
        match.match_status = MatchStatus.REJECTED
        match.match_decision = MatchDecision.DISPUTE
        match.decided_by = user_id
        match.decided_at = datetime.utcnow()
        if notes:
            match.notes = notes
        
        self.db.commit()
        self.db.refresh(match)
        
        logger.info(f"Rejected match {match_id}")
        return match
