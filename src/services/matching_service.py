// src/services/matching_service.py
from typing import List, Optional, Dict, Tuple
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from uuid import UUID
from src.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine, POStatus
from src.models.delivery_note import DeliveryNote, DeliveryNoteLine, DeliveryNoteStatus
from src.models.match import Match, MatchLine, MatchStatus, MatchDecision
from src.config import get_settings

settings = get_settings()


class MatchingService:
    """
    3-Way Matching Engine
    Layer 1: Anchor PO by supplier + PO number
    Layer 2: Cascade matching with weighted scoring
    Layer 3: Balance resolution for partial matches
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.line_weight = Decimal(str(settings.match_line_weight))
        self.amount_weight = Decimal(str(settings.match_amount_weight))
        self.date_weight = Decimal(str(settings.match_date_weight))
        self.auto_approve_threshold = Decimal(str(settings.match_auto_approve_threshold))
        self.human_review_threshold = Decimal(str(settings.match_human_review_threshold))
    
    def find_po_by_supplier_and_number(
        self,
        supplier_code: str,
        invoice_number: str = None
    ) -> Optional[PurchaseOrder]:
        """Layer 1: Find anchoring PO"""
        query = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.lines)
        ).filter(
            and_(
                PurchaseOrder.supplier_code == supplier_code,
                PurchaseOrder.status.in_([POStatus.APPROVED, POStatus.PARTIALLY_RECEIVED])
            )
        )
        
        if invoice_number:
            po = query.filter(
                or_(
                    PurchaseOrder.po_number.like(f"%{invoice_number}%"),
                    PurchaseOrder.notes.like(f"%{invoice_number}%")
                )
            ).first()
            if po:
                return po
        
        return query.first()
    
    def find_matching_dn(
        self,
        supplier_code: str,
        purchase_order_id: UUID
    ) -> Optional[DeliveryNote]:
        """Find delivery note for PO"""
        return self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.lines)
        ).filter(
            and_(
                DeliveryNote.supplier_code == supplier_code,
                DeliveryNote.purchase_order_id == purchase_order_id,
                DeliveryNote.status == DeliveryNoteStatus.SUBMITTED
            )
        ).first()
    
    def calculate_line_match_score(
        self,
        invoice_line: InvoiceLine,
        po_lines: List[PurchaseOrderLine],
        dn_line: DeliveryNoteLine = None
    ) -> Tuple[Decimal, PurchaseOrderLine, Optional[DeliveryNoteLine]]:
        """Calculate line-level match score with product code matching"""
        best_score = Decimal("0.0000")
        best_po_line = None
        best_dn_line = None
        
        for po_line in po_lines:
            if invoice_line.product_code == po_line.product_code:
                qty_score = Decimal("1.0000")
                if dn_line and invoice_line.product_code == dn_line.product_code:
                    dn_qty_match = min(
                        float(invoice_line.quantity) / float(dn_line.quantity)
                        if dn_line.quantity > 0 else 0,
                        float(dn_line.quantity) / float(invoice_line.quantity)
                        if invoice_line.quantity > 0 else 0
                    )
                    qty_score = Decimal(str(min(qty_score, Decimal(str(dn_qty_match)))))
                else:
                    po_qty_match = min(
                        float(invoice_line.quantity) / float(po_line.quantity)
                        if po_line.quantity > 0 else 0,
                        float(po_line.quantity) / float(invoice_line.quantity)
                        if invoice_line.quantity > 0 else 0
                    )
                    qty_score = Decimal(str(min(Decimal("1.0000"), Decimal(str(po_qty_match)))))
                
                score = qty_score
                if score > best_score:
                    best_score = score
                    best_po_line = po_line
                    best_dn_line = dn_line
        
        if not best_po_line:
            for po_line in po_lines:
                if invoice_line.description.lower() in po_line.description.lower():
                    qty_match = min(
                        float(invoice_line.quantity) / float(po_line.quantity)
                        if po_line.quantity > 0 else 0,
                        1.0
                    )
                    score = Decimal(str(qty_match * 0.8))
                    if score > best_score:
                        best_score = score
                        best_po_line = po_line
        
        return best_score, best_po_line, best_dn_line
    
    def calculate_amount_score(
        self,
        invoice_amount: Decimal,
        po_amount: Decimal,
        dn_amount: Decimal = None
    ) -> Decimal:
        """Calculate amount match score"""
        if dn_amount:
            match_amount = min(invoice_amount, po_amount, dn_amount)
            max_amount = max(invoice_amount, po_amount, dn_amount)
        else:
            match_amount = min(invoice_amount, po_amount)
            max_amount = max(invoice_amount, po_amount)
        
        if max_amount == 0:
            return Decimal("1.0000")
        
        return match_amount / max_amount
    
    def calculate_date_score(self, invoice_date: date, po_date: date) -> Decimal:
        """Calculate date proximity score"""
        days_diff = abs((invoice_date - po_date).days)
        
        if days_diff <= 7:
            return Decimal("1.0000")
        elif days_diff <= 14:
            return Decimal("0.90")
        elif days_diff <= 30:
            return Decimal("0.80")
        elif days_diff <= 60:
            return Decimal("0.60")
        else:
            return Decimal("0.40")
    
    def calculate_overall_score(
        self,
        line_scores: List[Decimal],
        amount_score: Decimal,
        date_score: Decimal
    ) -> Decimal:
        """Calculate weighted overall match score"""
        if line_scores:
            avg_line_score = sum(line_scores) / len(line_scores)
        else:
            avg_line_score = Decimal("0.0000")
        
        overall = (
            avg_line_score * self.line_weight +
            amount_score * self.amount_weight +
            date_score * self.date_weight
        )
        
        return min(overall, Decimal("1.0000"))
    
    def determine_decision(self, score: Decimal) -> MatchDecision:
        """Determine match decision based on score"""
        if score >= self.auto_approve_threshold:
            return MatchDecision.AUTO_APPROVE
        elif score >= self.human_review_threshold:
            return MatchDecision.HUMAN_REVIEW
        else:
            return MatchDecision.DISPUTE
    
    def create_match(
        self,
        invoice: Invoice,
        purchase_order: PurchaseOrder,
        delivery_note: Optional[DeliveryNote],
        line_matches: List[Dict],
        overall_score: Decimal
    ) -> Match:
        """Create match record"""
        variance = abs(invoice.total_amount - purchase_order.total_amount)
        
        match_type = "three_way" if delivery_note else "invoice_po"
        
        db_match = Match(
            invoice_id=invoice.id,
            purchase_order_id=purchase_order.id,
            delivery_note_id=delivery_note.id if delivery_note else None,
            match_type=match_type,
            match_score=overall_score,
            status=MatchStatus.PENDING,
            decision=self.determine_decision(overall_score),
            invoice_amount=invoice.total_amount,
            po_amount=purchase_order.total_amount,
            variance_amount=variance
        )
        
        if overall_score >= self.auto_approve_threshold:
            db_match.status = MatchStatus.CONFIRMED
        
        self.db.add(db_match)
        self.db.flush()
        
        for line_match in line_matches:
            db_line = MatchLine(
                match_id=db_match.id,
                invoice_line_id=line_match.get("invoice_line_id"),
                po_line_id=line_match.get("po_line_id"),
                dn_line_id=line_match.get("dn_line_id"),
                product_code=line_match["product_code"],
                invoice_quantity=line_match.get("invoice_quantity"),
                po_quantity=line_match.get("po_quantity"),
                dn_quantity=line_match.get("dn_quantity"),
                line_match_score=line_match["score"],
                quantity_variance=line_match.get("variance", Decimal("0.0000"))
            )
            self.db.add(db_line)
        
        return db_match
    
    def perform_three_way_match(
        self,
        invoice_id: str,
        delivery_note_id: Optional[str] = None,
        user_id: str = None
    ) -> List[Match]:
        """Perform complete 3-way matching"""
        invoice = self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        if invoice.status == InvoiceStatus.MATCHED:
            raise ValueError("Invoice is already matched")
        
        po = self.find_po_by_supplier_and_number(
            supplier_code=invoice.supplier_code,
            invoice_number=invoice.invoice_number
        )
        
        if not po:
            raise ValueError("No matching Purchase Order found")
        
        delivery_note = None
        if delivery_note_id:
            delivery_note = self.db.query(DeliveryNote).options(
                joinedload(DeliveryNote.lines)
            ).filter(DeliveryNote.id == delivery_note_id).first()
        elif invoice.purchase_order_id == po.id:
            delivery_note = self.find_matching_dn(
                supplier_code=invoice.supplier_code,
                purchase_order_id=po.id
            )
        
        line_scores = []
        line_matches = []
        
        for inv_line in invoice.lines:
            score, po_line, dn_line = self.calculate_line_match_score(
                inv_line,
                po.lines,
                dn_line=delivery_note.lines[0] if delivery_note and delivery_note.lines else None
            )
            
            line_scores.append(score)
            
            if po_line:
                qty_variance = abs(inv_line.quantity - po_line.quantity)
                line_matches.append({
                    "invoice_line_id": inv_line.id,
                    "po_line_id": po_line.id,
                    "dn_line_id": dn_line.id if dn_line else None,
                    "product_code": inv_line.product_code or po_line.product_code,
                    "invoice_quantity": inv_line.quantity,
                    "po_quantity": po_line.quantity,
                    "dn_quantity": dn_line.quantity if dn_line else None,
                    "score": score,
                    "variance": qty_variance
                })
        
        amount_score = self.calculate_amount_score(
            invoice.total_amount,
            po.total_amount,
            delivery_note.total_amount if delivery_note else None
        )
        
        date_score = self.calculate_date_score(
            invoice.invoice_date,
            po.order_date
        )
        
        overall_score = self.calculate_overall_score(line_scores, amount_score, date_score)
        
        match = self.create_match(
            invoice=invoice,
            purchase_order=po,
            delivery_note=delivery_note,
            line_matches=line_matches,
            overall_score=overall_score
        )
        
        if match.status == MatchStatus.CONFIRMED:
            invoice.status = InvoiceStatus.APPROVED
        elif match.decision == MatchDecision.HUMAN_REVIEW:
            invoice.status = InvoiceStatus.PENDING_APPROVAL
        else:
            invoice.status = InvoiceStatus.REJECTED
        
        self.db.commit()
        self.db.refresh(match)
        
        return [match]
    
    def auto_match_pending_invoices(self, user_id: str) -> List[Match]:
        """Auto-match all pending invoices"""
        pending_invoices = self.db.query(Invoice).filter(
            Invoice.status == InvoiceStatus.SUBMITTED
        ).all()
        
        matches = []
        for invoice in pending_invoices:
            try:
                result = self.perform_three_way_match(
                    invoice_id=str(invoice.id),
                    user_id=user_id
                )
                matches.extend(result)
            except ValueError:
                continue
        
        return matches
