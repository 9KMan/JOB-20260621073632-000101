// src/services/matching_service.py
"""Core matching service implementing 3-layer matching architecture."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from src.app.config import get_settings
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.models.matching import (
    MatchingRecord, MatchType, MatchStatus, MatchDecision, MatchConfidenceLevel
)
from src.services.balance_service import BalanceService

settings = get_settings()


class MatchingService:
    """
    3-Way Matching Engine implementing the layered architecture.
    
    Layer 1 - Anchoring: Uses PO as single source of truth
    Layer 2 - Cascade Matching: Invoice↔PO, Delivery↔PO, Invoice↔Delivery
    Layer 3 - Balance Resolution: Track partial matches and balances
    """

    def __init__(self, db: Session):
        self.db = db
        self.balance_service = BalanceService(db)

    def find_po_anchor(
        self, 
        supplier_id: str, 
        po_number: Optional[str] = None
    ) -> Optional[PurchaseOrder]:
        """
        Layer 1: Find PO anchor for incoming documents.
        Returns the PO that will serve as the anchor for matching.
        """
        query = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.status.in_([
                    PurchaseOrderStatus.APPROVED,
                    PurchaseOrderStatus.PARTIALLY_MATCHED
                ])
            )
        )
        
        if po_number:
            query = query.filter(PurchaseOrder.po_number == po_number)
        
        # Prefer POs that are partially matched (active relationships)
        query = query.order_by(
            PurchaseOrder.status == PurchaseOrderStatus.PARTIALLY_MATCHED,
            PurchaseOrder.order_date.desc()
        )
        
        return query.first()

    def match_invoice_to_po(
        self, 
        invoice: Invoice, 
        po: PurchaseOrder
    ) -> MatchingRecord:
        """
        Layer 2: Match invoice to PO.
        Calculates weighted score: line-level (70%), amount (20%), date (10%).
        """
        # Get line scores
        line_score = self._calculate_line_level_score(
            invoice.lines, po.lines
        )
        
        # Get amount score
        amount_score = self._calculate_amount_score(
            invoice.total_amount, po.total_amount
        )
        
        # Get date score
        date_score = self._calculate_date_score(
            invoice.invoice_date, po.order_date
        )
        
        # Calculate weighted overall score
        overall_score = (
            line_score * Decimal(str(settings.MATCHING_WEIGHT_LINE_LEVEL)) +
            amount_score * Decimal(str(settings.MATCHING_WEIGHT_AMOUNT)) +
            date_score * Decimal(str(settings.MATCHING_WEIGHT_DATE))
        )
        
        # Determine variance
        variance_amount = abs(invoice.total_amount - po.total_amount)
        variance_percentage = (
            variance_amount / po.total_amount 
            if po.total_amount > 0 else Decimal("0")
        )
        
        # Determine decision based on thresholds
        decision = self._determine_decision(overall_score, variance_percentage)
        confidence_level = self._get_confidence_level(overall_score)
        
        # Create matching record
        matching_record = MatchingRecord(
            match_type=MatchType.PO_INVOICE.value,
            status=MatchStatus.PENDING.value,
            decision=decision,
            overall_score=overall_score,
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            confidence_level=confidence_level,
            purchase_order_id=po.id,
            invoice_id=invoice.id,
            po_amount=po.total_amount,
            invoice_amount=invoice.total_amount,
            matched_amount=min(invoice.total_amount, po.total_amount),
            variance_amount=variance_amount,
            line_match_details=self._get_line_match_details(invoice.lines, po.lines)
        )
        
        self.db.add(matching_record)
        self.db.flush()
        
        return matching_record

    def match_delivery_to_po(
        self, 
        delivery_note: DeliveryNote, 
        po: PurchaseOrder
    ) -> MatchingRecord:
        """
        Layer 2: Match delivery note to PO.
        """
        # Calculate line scores for quantities
        line_score = self._calculate_quantity_line_score(
            delivery_note.lines, po.lines
        )
        
        # Amount score based on delivered vs ordered
        expected_delivery_value = sum(
            line.delivered_quantity * line.unit_price 
            for line in delivery_note.lines
            if hasattr(line, 'unit_price') and line.unit_price
        ) or Decimal("0")
        
        amount_score = self._calculate_amount_score(
            expected_delivery_value, po.total_amount
        )
        
        date_score = self._calculate_date_score(
            delivery_note.delivery_date, po.expected_delivery_date or po.order_date
        )
        
        overall_score = (
            line_score * Decimal(str(settings.MATCHING_WEIGHT_LINE_LEVEL)) +
            amount_score * Decimal(str(settings.MATCHING_WEIGHT_AMOUNT)) +
            date_score * Decimal(str(settings.MATCHING_WEIGHT_DATE))
        )
        
        variance_amount = abs(expected_delivery_value - po.total_amount)
        
        decision = self._determine_decision(overall_score, variance_amount / po.total_amount if po.total_amount > 0 else Decimal("0"))
        confidence_level = self._get_confidence_level(overall_score)
        
        matching_record = MatchingRecord(
            match_type=MatchType.PO_DELIVERY.value,
            status=MatchStatus.PENDING.value,
            decision=decision,
            overall_score=overall_score,
            line_level_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            confidence_level=confidence_level,
            purchase_order_id=po.id,
            delivery_note_id=delivery_note.id,
            po_amount=po.total_amount,
            delivery_amount=expected_delivery_value,
            matched_amount=expected_delivery_value,
            variance_amount=variance_amount,
            line_match_details=self._get_delivery_line_match_details(delivery_note.lines, po.lines)
        )
        
        self.db.add(matching_record)
        self.db.flush()
        
        return matching_record

    def perform_three_way_match(
        self,
        invoice: Invoice,
        delivery_note: DeliveryNote,
        po: PurchaseOrder
    ) -> MatchingRecord:
        """
        Layer 2: Full three-way match.
        Matches all three documents together.
        """
        # Match each document to PO
        po_invoice_score = self._calculate_line_level_score(
            invoice.lines, po.lines
        )
        po_delivery_score = self._calculate_quantity_line_score(
            delivery_note.lines, po.lines
        )
        
        # Match invoice to delivery
        invoice_delivery_score = self._calculate_invoice_delivery_score(
            invoice.lines, delivery_note.lines
        )
        
        # Combined score (average of all three pairwise matches)
        overall_score = (po_invoice_score + po_delivery_score + invoice_delivery_score) / 3
        
        # Amount comparison across all three
        invoice_amount = invoice.total_amount
        delivery_value = sum(
            line.delivered_quantity * (line.ordered_quantity / line.delivered_quantity * Decimal("1"))
            for line in delivery_note.lines
        ) or delivery_note.lines[0].delivered_quantity if delivery_note.lines else Decimal("0")
        
        amount_score = self._calculate_amount_score(
            invoice_amount, po.total_amount
        )
        
        # Variance calculation
        variance_amount = max(
            abs(invoice_amount - po.total_amount),
            abs(delivery_value - po.total_amount)
        )
        
        decision = self._determine_decision(overall_score, variance_amount / po.total_amount if po.total_amount > 0 else Decimal("0"))
        confidence_level = self._get_confidence_level(overall_score)
        
        # Create three-way matching record
        matching_record = MatchingRecord(
            match_type=MatchType.THREE_WAY.value,
            status=MatchStatus.PENDING.value,
            decision=decision,
            overall_score=overall_score,
            line_level_score=overall_score,
            amount_score=amount_score,
            date_score=Decimal("1.0"),
            confidence_level=confidence_level,
            purchase_order_id=po.id,
            invoice_id=invoice.id,
            delivery_note_id=delivery_note.id,
            po_amount=po.total_amount,
            invoice_amount=invoice_amount,
            delivery_amount=delivery_value,
            matched_amount=min(invoice_amount, po.total_amount, delivery_value),
            variance_amount=variance_amount,
            line_match_details=self._get_three_way_line_details(
                invoice.lines, delivery_note.lines, po.lines
            )
        )
        
        self.db.add(matching_record)
        self.db.flush()
        
        # Layer 3: Create balance entries for variances
        if variance_amount > 0:
            self.balance_service.create_balance_for_variance(
                matching_record=matching_record,
                variance_amount=variance_amount
            )
        
        return matching_record

    def _calculate_line_level_score(
        self, 
        invoice_lines: list, 
        po_lines: list
    ) -> Decimal:
        """Calculate line-level match score (70% weight)."""
        if not po_lines:
            return Decimal("0.0")
        
        matched_lines = 0
        total_lines = len(po_lines)
        
        for po_line in po_lines:
            for inv_line in invoice_lines:
                if self._lines_match(po_line, inv_line):
                    matched_lines += 1
                    break
        
        return Decimal(str(matched_lines / total_lines))

    def _calculate_quantity_line_score(
        self, 
        delivery_lines: list, 
        po_lines: list
    ) -> Decimal:
        """Calculate quantity-based line score for delivery matching."""
        if not po_lines:
            return Decimal("0.0")
        
        total_score = Decimal("0.0")
        for po_line in po_lines:
            best_match_score = Decimal("0.0")
            for del_line in delivery_lines:
                if del_line.item_code == po_line.item_code:
                    # Calculate quantity match percentage
                    if po_line.quantity > 0:
                        match_ratio = min(del_line.delivered_quantity, po_line.quantity) / po_line.quantity
                        best_match_score = max(best_match_score, match_ratio)
            total_score += best_match_score
        
        return total_score / Decimal(str(len(po_lines))) if po_lines else Decimal("0.0")

    def _calculate_invoice_delivery_score(
        self, 
        invoice_lines: list, 
        delivery_lines: list
    ) -> Decimal:
        """Calculate invoice to delivery line score."""
        if not delivery_lines:
            return Decimal("0.0")
        
        total_score = Decimal("0.0")
        for inv_line in invoice_lines:
            best_match_score = Decimal("0.0")
            for del_line in delivery_lines:
                if del_line.item_code == inv_line.item_code:
                    if inv_line.quantity > 0:
                        match_ratio = min(del_line.delivered_quantity, inv_line.quantity) / inv_line.quantity
                        best_match_score = max(best_match_score, match_ratio)
            total_score += best_match_score
        
        return total_score / Decimal(str(len(invoice_lines))) if invoice_lines else Decimal("0.0")

    def _lines_match(self, po_line: PurchaseOrderLine, inv_line: InvoiceLine) -> bool:
        """Check if PO line and invoice line match."""
        return (
            po_line.item_code == inv_line.item_code and
            abs(po_line.quantity - inv_line.quantity) <= Decimal(str(settings.MATCHING_TOLERANCE_AMOUNT))
        )

    def _calculate_amount_score(
        self, 
        amount1: Decimal, 
        amount2: Decimal
    ) -> Decimal:
        """Calculate amount match score (20% weight)."""
        if amount2 == 0:
            return Decimal("0.0") if amount1 != 0 else Decimal("1.0")
        
        variance = abs(amount1 - amount2) / amount2
        score = max(Decimal("0.0"), Decimal("1.0") - Decimal(str(variance)))
        return score

    def _calculate_date_score(
        self, 
        date1: date, 
        date2: date
    ) -> Decimal:
        """Calculate date proximity score (10% weight)."""
        if not date1 or not date2:
            return Decimal("0.5")
        
        days_diff = abs((date1 - date2).days)
        
        # Perfect match
        if days_diff == 0:
            return Decimal("1.0")
        # Within a week
        elif days_diff <= 7:
            return Decimal("0.9")
        # Within a month
        elif days_diff <= 30:
            return Decimal("0.7")
        # Within 3 months
        elif days_diff <= 90:
            return Decimal("0.5")
        else:
            return Decimal("0.3")

    def _determine_decision(
        self, 
        score: Decimal, 
        variance_percentage: Decimal
    ) -> str:
        """Determine matching decision based on score and variance."""
        tolerance = Decimal(str(settings.MATCHING_TOLERANCE_PERCENT))
        
        if score >= Decimal(str(settings.MATCHING_AUTO_APPROVE_THRESHOLD)) and variance_percentage <= tolerance:
            return MatchDecision.AUTO_APPROVED.value
        elif score >= Decimal(str(settings.MATCHING_HUMAN_REVIEW_THRESHOLD)):
            return MatchDecision.HUMAN_REVIEW.value
        else:
            return MatchDecision.REJECTED.value

    def _get_confidence_level(self, score: Decimal) -> str:
        """Get confidence level based on score."""
        if score >= Decimal("0.90"):
            return MatchConfidenceLevel.HIGH.value
        elif score >= Decimal("0.70"):
            return MatchConfidenceLevel.MEDIUM.value
        else:
            return MatchConfidenceLevel.LOW.value

    def _get_line_match_details(
        self, 
        invoice_lines: list, 
        po_lines: list
    ) -> dict:
        """Get detailed line matching information."""
        details = []
        for po_line in po_lines:
            matched_inv_line = None
            for inv_line in invoice_lines:
                if self._lines_match(po_line, inv_line):
                    matched_inv_line = inv_line
                    break
            
            details.append({
                "po_line_id": str(po_line.id),
                "item_code": po_line.item_code,
                "po_quantity": float(po_line.quantity),
                "invoice_quantity": float(matched_inv_line.quantity) if matched_inv_line else 0,
                "matched": matched_inv_line is not None
            })
        
        return {"line_details": details}

    def _get_delivery_line_match_details(
        self, 
        delivery_lines: list, 
        po_lines: list
    ) -> dict:
        """Get detailed delivery line matching information."""
        details = []
        for po_line in po_lines:
            matched_del_line = None
            for del_line in delivery_lines:
                if del_line.item_code == po_line.item_code:
                    matched_del_line = del_line
                    break
            
            details.append({
                "po_line_id": str(po_line.id),
                "item_code": po_line.item_code,
                "po_quantity": float(po_line.quantity),
                "delivered_quantity": float(matched_del_line.delivered_quantity) if matched_del_line else 0,
                "matched": matched_del_line is not None
            })
        
        return {"line_details": details}

    def _get_three_way_line_details(
        self, 
        invoice_lines: list, 
        delivery_lines: list, 
        po_lines: list
    ) -> dict:
        """Get detailed three-way line matching information."""
        details = []
        for po_line in po_lines:
            matched_inv_line = None
            matched_del_line = None
            
            for inv_line in invoice_lines:
                if self._lines_match(po_line, inv_line):
                    matched_inv_line = inv_line
                    break
            
            for del_line in delivery_lines:
                if del_line.item_code == po_line.item_code:
                    matched_del_line = del_line
                    break
            
            details.append({
                "po_line_id": str(po_line.id),
                "item_code": po_line.item_code,
                "po_quantity": float(po_line.quantity),
                "invoice_quantity": float(matched_inv_line.quantity) if matched_inv_line else 0,
                "delivery_quantity": float(matched_del_line.delivered_quantity) if matched_del_line else 0,
                "all_matched": matched_inv_line is not None and matched_del_line is not None
            })
        
        return {"line_details": details}

    def process_match_decision(
        self, 
        matching_record_id: UUID, 
        decision: str, 
        user_id: UUID,
        notes: Optional[str] = None,
        rejection_reason: Optional[str] = None
    ) -> MatchingRecord:
        """
        Process human decision on a matching record.
        Updates the record and feeds back into the learning loop.
        """
        matching_record = self.db.query(MatchingRecord).filter(
            MatchingRecord.id == matching_record_id
        ).first()
        
        if not matching_record:
            raise ValueError(f"Matching record {matching_record_id} not found")
        
        matching_record.decision = decision
        matching_record.status = MatchStatus.MATCHED.value if decision == MatchDecision.AUTO_APPROVED.value else MatchStatus.PENDING.value
        matching_record.confirmed_by_id = user_id
        matching_record.confirmed_at = datetime.utcnow()
        
        if notes:
            matching_record.review_notes = notes
        if rejection_reason:
            matching_record.rejection_reason = rejection_reason
        
        # Update source documents based on decision
        if decision == MatchDecision.AUTO_APPROVED.value:
            self._approve_match(matching_record)
        elif decision == MatchDecision.REJECTED.value:
            self._reject_match(matching_record)
        
        self.db.flush()
        return matching_record

    def _approve_match(self, matching_record: MatchingRecord) -> None:
        """Approve and settle the match."""
        # Update PO paid amount
        if matching_record.purchase_order_id:
            po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == matching_record.purchase_order_id
            ).first()
            if po:
                po.paid_amount += matching_record.matched_amount
                po.calculate_remaining_amount()
                
                if po.remaining_amount <= 0:
                    po.status = PurchaseOrderStatus.FULLY_MATCHED.value
                else:
                    po.status = PurchaseOrderStatus.PARTIALLY_MATCHED.value
        
        # Update invoice status
        if matching_record.invoice_id:
            invoice = self.db.query(Invoice).filter(
                Invoice.id == matching_record.invoice_id
            ).first()
            if invoice:
                invoice.status = InvoiceStatus.APPROVED.value
                invoice.approved_at = datetime.utcnow()
        
        # Update delivery note status
        if matching_record.delivery_note_id:
            delivery = self.db.query(DeliveryNote).filter(
                DeliveryNote.id == matching_record.delivery_note_id
            ).first()
            if delivery:
                delivery.status = DeliveryNoteStatus.APPROVED.value
                delivery.approved_at = datetime.utcnow()

    def _reject_match(self, matching_record: MatchingRecord) -> None:
        """Reject the match and mark for dispute."""
        matching_record.status = MatchStatus.DISPUTED.value
        
        if matching_record.invoice_id:
            invoice = self.db.query(Invoice).filter(
                Invoice.id == matching_record.invoice_id
            ).first()
            if invoice:
                invoice.status = InvoiceStatus.DISPUTED.value
        
        if matching_record.delivery_note_id:
            delivery = self.db.query(DeliveryNote).filter(
                DeliveryNote.id == matching_record.delivery_note_id
            ).first()
            if delivery:
                delivery.status = DeliveryNoteStatus.REJECTED.value

    def get_match_candidates(
        self, 
        document_type: str, 
        document_id: UUID
    ) -> list[dict]:
        """Find potential match candidates for a document."""
        candidates = []
        
        if document_type == "invoice":
            invoice = self.db.query(Invoice).filter(Invoice.id == document_id).first()
            if invoice:
                # Find POs by supplier
                pos = self.db.query(PurchaseOrder).filter(
                    and_(
                        PurchaseOrder.supplier_id == invoice.supplier_id,
                        PurchaseOrder.status.in_([
                            PurchaseOrderStatus.APPROVED,
                            PurchaseOrderStatus.PARTIALLY_MATCHED
                        ])
                    )
                ).all()
                
                for po in pos:
                    score = self._calculate_line_level_score(invoice.lines, po.lines)
                    candidates.append({
                        "po_id": str(po.id),
                        "po_number": po.po_number,
                        "score": float(score),
                        "match_type": "po_invoice"
                    })
        
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def get_matching_summary(self) -> dict:
        """Get summary statistics for matching."""
        total = self.db.query(MatchingRecord).count()
        auto_approved = self.db.query(MatchingRecord).filter(
            MatchingRecord.decision == MatchDecision.AUTO_APPROVED.value
        ).count()
        pending = self.db.query(MatchingRecord).filter(
            MatchingRecord.decision == MatchDecision.HUMAN_REVIEW.value
        ).count()
        rejected = self.db.query(MatchingRecord).filter(
            MatchingRecord.decision == MatchDecision.REJECTED.value
        ).count()
        unmatched = self.db.query(MatchingRecord).filter(
            MatchingRecord.status == MatchStatus.UNMATCHED.value
        ).count()
        
        avg_score = self.db.query(MatchingRecord.overall_score).all()
        avg_score_value = (
            sum(float(s[0]) for s in avg_score) / len(avg_score) 
            if avg_score else 0.0
        )
        
        return {
            "total_records": total,
            "auto_approved": auto_approved,
            "pending_review": pending,
            "rejected": rejected,
            "unmatched": unmatched,
            "average_score": avg_score_value
        }
