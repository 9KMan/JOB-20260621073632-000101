// src/services/matching_service.py
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from src.models.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    Invoice,
    InvoiceLine,
    DeliveryNote,
    DeliveryNoteLine,
    MatchRecord,
    BalanceRecord,
    MatchType,
    MatchStatus,
    DocumentStatus,
)
from src.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MatchingService:
    """Service for performing 3-way matching between PO, Invoice, and Delivery Note."""

    def __init__(self, db: Session):
        self.db = db
        self.weights = {
            "line_level": settings.MATCH_WEIGHT_LINE_LEVEL,
            "amount": settings.MATCH_WEIGHT_AMOUNT,
            "date": settings.MATCH_WEIGHT_DATE,
        }

    def find_anchor_po(self, supplier_id: UUID, po_reference: str) -> Optional[PurchaseOrder]:
        """
        Layer 1: Find the anchor PO for a document.
        
        Uses the PO number and supplier to establish a deterministic anchor.
        """
        po = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.po_number == po_reference,
                PurchaseOrder.is_closed == False,
            )
        ).first()
        
        if po:
            logger.info(f"Found anchor PO: {po.po_number} for supplier {supplier_id}")
        
        return po

    def match_po_invoice(
        self, po: PurchaseOrder, invoice: Invoice
    ) -> Tuple[MatchRecord, Dict[str, Any]]:
        """
        Match a Purchase Order with an Invoice.
        
        Returns the match record and scoring details.
        """
        logger.info(f"Matching PO {po.po_number} with Invoice {invoice.invoice_number}")
        
        # Calculate scores
        line_score = self._calculate_line_level_score_po_invoice(po, invoice)
        amount_score = self._calculate_amount_score(po.total_amount, invoice.net_amount)
        date_score = self._calculate_date_score(po.order_date, invoice.invoice_date)
        total_score = self._calculate_weighted_score(line_score, amount_score, date_score)
        
        # Calculate variance
        variance = float(Decimal(str(po.total_amount)) - Decimal(str(invoice.net_amount)))
        
        # Get matched lines
        matched_lines = self._get_matched_po_invoice_lines(po, invoice)
        
        # Create match record
        match_record = MatchRecord(
            po_id=po.id,
            invoice_id=invoice.id,
            match_type=MatchType.PO_INVOICE,
            status=MatchStatus.PENDING,
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            total_score=total_score,
            po_amount=po.total_amount,
            invoice_amount=invoice.net_amount,
            variance_amount=variance,
            matched_lines=json.dumps(matched_lines),
        )
        
        self.db.add(match_record)
        self.db.flush()
        
        scoring_details = {
            "line_level_score": line_score,
            "amount_score": amount_score,
            "date_score": date_score,
            "total_score": total_score,
            "variance": variance,
            "matched_lines_count": len(matched_lines),
        }
        
        return match_record, scoring_details

    def match_po_delivery(
        self, po: PurchaseOrder, delivery_note: DeliveryNote
    ) -> Tuple[MatchRecord, Dict[str, Any]]:
        """
        Match a Purchase Order with a Delivery Note.
        """
        logger.info(f"Matching PO {po.po_number} with DN {delivery_note.dn_number}")
        
        line_score = self._calculate_line_level_score_po_dn(po, delivery_note)
        amount_score = self._calculate_amount_score(po.total_amount, delivery_note.total_amount)
        date_score = self._calculate_date_score(
            po.expected_delivery_date, delivery_note.delivery_date
        )
        total_score = self._calculate_weighted_score(line_score, amount_score, date_score)
        
        variance = float(Decimal(str(po.total_amount)) - Decimal(str(delivery_note.total_amount)))
        matched_lines = self._get_matched_po_dn_lines(po, delivery_note)
        
        match_record = MatchRecord(
            po_id=po.id,
            dn_id=delivery_note.id,
            match_type=MatchType.PO_DELIVERY,
            status=MatchStatus.PENDING,
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            total_score=total_score,
            po_amount=po.total_amount,
            dn_amount=delivery_note.total_amount,
            variance_amount=variance,
            matched_lines=json.dumps(matched_lines),
        )
        
        self.db.add(match_record)
        self.db.flush()
        
        scoring_details = {
            "line_level_score": line_score,
            "amount_score": amount_score,
            "date_score": date_score,
            "total_score": total_score,
            "variance": variance,
            "matched_lines_count": len(matched_lines),
        }
        
        return match_record, scoring_details

    def match_invoice_delivery(
        self, invoice: Invoice, delivery_note: DeliveryNote
    ) -> Tuple[MatchRecord, Dict[str, Any]]:
        """
        Match an Invoice with a Delivery Note.
        """
        logger.info(f"Matching Invoice {invoice.invoice_number} with DN {delivery_note.dn_number}")
        
        line_score = self._calculate_line_level_score_invoice_dn(invoice, delivery_note)
        amount_score = self._calculate_amount_score(invoice.net_amount, delivery_note.total_amount)
        date_score = self._calculate_date_score(invoice.invoice_date, delivery_note.delivery_date)
        total_score = self._calculate_weighted_score(line_score, amount_score, date_score)
        
        variance = float(
            Decimal(str(invoice.net_amount)) - Decimal(str(delivery_note.total_amount))
        )
        matched_lines = self._get_matched_invoice_dn_lines(invoice, delivery_note)
        
        match_record = MatchRecord(
            invoice_id=invoice.id,
            dn_id=delivery_note.id,
            match_type=MatchType.INVOICE_DELIVERY,
            status=MatchStatus.PENDING,
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            total_score=total_score,
            invoice_amount=invoice.net_amount,
            dn_amount=delivery_note.total_amount,
            variance_amount=variance,
            matched_lines=json.dumps(matched_lines),
        )
        
        self.db.add(match_record)
        self.db.flush()
        
        scoring_details = {
            "line_level_score": line_score,
            "amount_score": amount_score,
            "date_score": date_score,
            "total_score": total_score,
            "variance": variance,
            "matched_lines_count": len(matched_lines),
        }
        
        return match_record, scoring_details

    def perform_three_way_match(
        self, po: PurchaseOrder, invoice: Invoice, delivery_note: DeliveryNote
    ) -> Tuple[MatchRecord, Dict[str, Any]]:
        """
        Perform a complete 3-way match.
        
        This combines scores from all three pairwise matches.
        """
        logger.info(
            f"Performing 3-way match: PO {po.po_number}, "
            f"Invoice {invoice.invoice_number}, DN {delivery_note.dn_number}"
        )
        
        # Match each pair
        po_invoice_record, _ = self.match_po_invoice(po, invoice)
        po_dn_record, _ = self.match_po_delivery(po, delivery_note)
        invoice_dn_record, _ = self.match_invoice_delivery(invoice, delivery_note)
        
        # Average the scores for 3-way match
        avg_line_score = (
            po_invoice_record.line_level_score
            + po_dn_record.line_level_score
            + invoice_dn_record.line_level_score
        ) / 3
        
        avg_amount_score = (
            po_invoice_record.amount_score
            + po_dn_record.amount_score
            + invoice_dn_record.amount_score
        ) / 3
        
        avg_date_score = (
            po_invoice_record.date_score
            + po_dn_record.date_score
            + invoice_dn_record.date_score
        ) / 3
        
        total_score = self._calculate_weighted_score(
            avg_line_score, avg_amount_score, avg_date_score
        )
        
        # Calculate total variance
        total_variance = (
            float(po.total_amount)
            - float(invoice.net_amount)
            - float(delivery_note.total_amount)
        ) / 3
        
        # Create 3-way match record
        three_way_record = MatchRecord(
            po_id=po.id,
            invoice_id=invoice.id,
            dn_id=delivery_note.id,
            match_type=MatchType.THREE_WAY,
            status=MatchStatus.PENDING,
            line_level_score=avg_line_score,
            amount_score=avg_amount_score,
            date_score=avg_date_score,
            total_score=total_score,
            po_amount=po.total_amount,
            invoice_amount=invoice.net_amount,
            dn_amount=delivery_note.total_amount,
            variance_amount=total_variance,
        )
        
        self.db.add(three_way_record)
        self.db.flush()
        
        # Link related matches
        three_way_record.matched_lines = json.dumps({
            "po_invoice": str(po_invoice_record.id),
            "po_dn": str(po_dn_record.id),
            "invoice_dn": str(invoice_dn_record.id),
        })
        
        scoring_details = {
            "three_way_match_id": str(three_way_record.id),
            "component_matches": {
                "po_invoice": str(po_invoice_record.id),
                "po_dn": str(po_dn_record.id),
                "invoice_dn": str(invoice_dn_record.id),
            },
            "average_scores": {
                "line_level": avg_line_score,
                "amount": avg_amount_score,
                "date": avg_date_score,
                "total": total_score,
            },
        }
        
        return three_way_record, scoring_details

    def cascade_match_document(
        self, document_type: str, document_id: UUID
    ) -> List[MatchRecord]:
        """
        Layer 2: Cascade matching - find all potential matches for a document.
        """
        logger.info(f"Starting cascade match for {document_type} {document_id}")
        matches = []
        
        if document_type == "invoice":
            invoice = self.db.query(Invoice).filter(Invoice.id == document_id).first()
            if not invoice:
                return matches
            
            # Find anchor PO
            po = None
            if invoice.po_reference:
                po = self.find_anchor_po(invoice.supplier_id, invoice.po_reference)
            
            if po:
                # Match with PO
                match, _ = self.match_po_invoice(po, invoice)
                matches.append(match)
                
                # Find delivery notes for this PO
                dns = self.db.query(DeliveryNote).filter(
                    and_(
                        DeliveryNote.supplier_id == invoice.supplier_id,
                        DeliveryNote.po_reference == po.po_number,
                    )
                ).all()
                
                for dn in dns:
                    # Match invoice with DN
                    match, _ = self.match_invoice_delivery(invoice, dn)
                    matches.append(match)
                    
                    # Create 3-way match
                    three_way, _ = self.perform_three_way_match(po, invoice, dn)
                    matches.append(three_way)
            
        elif document_type == "delivery_note":
            dn = self.db.query(DeliveryNote).filter(DeliveryNote.id == document_id).first()
            if not dn:
                return matches
            
            po = None
            if dn.po_reference:
                po = self.find_anchor_po(dn.supplier_id, dn.po_reference)
            
            if po:
                match, _ = self.match_po_delivery(po, dn)
                matches.append(match)
                
                # Find invoices for this PO
                invoices = self.db.query(Invoice).filter(
                    and_(
                        Invoice.supplier_id == dn.supplier_id,
                        Invoice.po_reference == po.po_number,
                    )
                ).all()
                
                for inv in invoices:
                    match, _ = self.match_invoice_delivery(inv, dn)
                    matches.append(match)
                    three_way, _ = self.perform_three_way_match(po, inv, dn)
                    matches.append(three_way)
        
        return matches

    def _calculate_line_level_score_po_invoice(
        self, po: PurchaseOrder, invoice: Invoice
    ) -> float:
        """Calculate line-level matching score between PO and Invoice."""
        po_lines = {line.product_code: line for line in po.lines}
        invoice_lines = list(invoice.lines)
        
        if not invoice_lines:
            return 0.0
        
        matched_count = 0
        for inv_line in invoice_lines:
            if inv_line.product_code in po_lines:
                po_line = po_lines[inv_line.product_code]
                # Check quantity match (with tolerance)
                qty_ratio = min(inv_line.quantity, po_line.quantity) / max(
                    inv_line.quantity, po_line.quantity
                ) if po_line.quantity > 0 else 0
                
                # Check price match
                price_ratio = min(inv_line.unit_price, po_line.unit_price) / max(
                    inv_line.unit_price, po_line.unit_price
                ) if po_line.unit_price > 0 else 0
                
                if qty_ratio >= 0.9 and price_ratio >= 0.95:
                    matched_count += 1
        
        return matched_count / len(invoice_lines) if invoice_lines else 0.0

    def _calculate_line_level_score_po_dn(
        self, po: PurchaseOrder, dn: DeliveryNote
    ) -> float:
        """Calculate line-level matching score between PO and DN."""
        po_lines = {line.product_code: line for line in po.lines}
        dn_lines = list(dn.lines)
        
        if not dn_lines:
            return 0.0
        
        matched_count = 0
        for dn_line in dn_lines:
            if dn_line.product_code in po_lines:
                po_line = po_lines[dn_line.product_code]
                qty_ratio = min(dn_line.quantity_accepted, po_line.quantity) / max(
                    dn_line.quantity_accepted, po_line.quantity
                ) if po_line.quantity > 0 else 0
                
                if qty_ratio >= 0.9:
                    matched_count += 1
        
        return matched_count / len(dn_lines) if dn_lines else 0.0

    def _calculate_line_level_score_invoice_dn(
        self, invoice: Invoice, dn: DeliveryNote
    ) -> float:
        """Calculate line-level matching score between Invoice and DN."""
        inv_lines = {line.product_code: line for line in invoice.lines}
        dn_lines = list(dn.lines)
        
        if not dn_lines:
            return 0.0
        
        matched_count = 0
        for dn_line in dn_lines:
            if dn_line.product_code in inv_lines:
                inv_line = inv_lines[dn_line.product_code]
                qty_ratio = min(dn_line.quantity_accepted, inv_line.quantity) / max(
                    dn_line.quantity_accepted, inv_line.quantity
                ) if inv_line.quantity > 0 else 0
                
                if qty_ratio >= 0.9:
                    matched_count += 1
        
        return matched_count / len(dn_lines) if dn_lines else 0.0

    def _calculate_amount_score(self, amount1: float, amount2: float) -> float:
        """Calculate amount matching score."""
        if amount1 == 0 and amount2 == 0:
            return 1.0
        
        if amount1 == 0 or amount2 == 0:
            return 0.0
        
        ratio = min(amount1, amount2) / max(amount1, amount2)
        
        # Apply tolerance
        tolerance = settings.BALANCE_TOLERANCE_PERCENT
        if abs(1 - ratio) <= tolerance:
            return 1.0
        
        return ratio

    def _calculate_date_score(self, date1: Optional[datetime], date2: datetime) -> float:
        """Calculate date proximity score."""
        if date1 is None:
            return 0.5  # Neutral if no expected date
        
        delta = abs((date1 - date2).days)
        
        if delta == 0:
            return 1.0
        elif delta <= 3:
            return 0.9
        elif delta <= 7:
            return 0.8
        elif delta <= 14:
            return 0.6
        elif delta <= 30:
            return 0.4
        else:
            return 0.2

    def _calculate_weighted_score(
        self, line_score: float, amount_score: float, date_score: float
    ) -> float:
        """Calculate weighted total score."""
        return (
            line_score * self.weights["line_level"]
            + amount_score * self.weights["amount"]
            + date_score * self.weights["date"]
        )

    def _get_matched_po_invoice_lines(
        self, po: PurchaseOrder, invoice: Invoice
    ) -> List[Dict[str, Any]]:
        """Get matched line details for PO-Invoice match."""
        po_lines = {line.product_code: line for line in po.lines}
        matched = []
        
        for inv_line in invoice.lines:
            if inv_line.product_code in po_lines:
                po_line = po_lines[inv_line.product_code]
                matched.append({
                    "product_code": inv_line.product_code,
                    "po_quantity": float(po_line.quantity),
                    "invoice_quantity": float(inv_line.quantity),
                    "po_price": float(po_line.unit_price),
                    "invoice_price": float(inv_line.unit_price),
                    "matched": True,
                })
            else:
                matched.append({
                    "product_code": inv_line.product_code,
                    "po_quantity": None,
                    "invoice_quantity": float(inv_line.quantity),
                    "matched": False,
                })
        
        return matched

    def _get_matched_po_dn_lines(
        self, po: PurchaseOrder, dn: DeliveryNote
    ) -> List[Dict[str, Any]]:
        """Get matched line details for PO-DN match."""
        po_lines = {line.product_code: line for line in po.lines}
        matched = []
        
        for dn_line in dn.lines:
            if dn_line.product_code in po_lines:
                po_line = po_lines[dn_line.product_code]
                matched.append({
                    "product_code": dn_line.product_code,
                    "po_quantity": float(po_line.quantity),
                    "dn_quantity_delivered": float(dn_line.quantity_delivered),
                    "dn_quantity_accepted": float(dn_line.quantity_accepted),
                    "matched": True,
                })
            else:
                matched.append({
                    "product_code": dn_line.product_code,
                    "matched": False,
                })
        
        return matched

    def _get_matched_invoice_dn_lines(
        self, invoice: Invoice, dn: DeliveryNote
    ) -> List[Dict[str, Any]]:
        """Get matched line details for Invoice-DN match."""
        inv_lines = {line.product_code: line for line in invoice.lines}
        matched = []
        
        for dn_line in dn.lines:
            if dn_line.product_code in inv_lines:
                inv_line = inv_lines[dn_line.product_code]
                matched.append({
                    "product_code": dn_line.product_code,
                    "invoice_quantity": float(inv_line.quantity),
                    "dn_quantity_delivered": float(dn_line.quantity_delivered),
                    "dn_quantity_accepted": float(dn_line.quantity_accepted),
                    "matched": True,
                })
            else:
                matched.append({
                    "product_code": dn_line.product_code,
                    "matched": False,
                })
        
        return matched
