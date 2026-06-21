# src/services/matching_service.py
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.orm import Session, joinedload

from src.app.config import settings
from src.models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from src.models.invoice import Invoice, InvoiceLineItem
from src.models.delivery_note import DeliveryNote, DeliveryNoteLineItem
from src.models.match import Match, MatchStatus, MatchType
from src.models.balance import Balance
from src.services.balance_service import BalanceService


class MatchingService:
    """Service for 3-way matching operations (Invoice × Delivery Note × PO)."""
    
    def __init__(self, db: Session):
        self.db = db
        self.balance_service = BalanceService(db)
    
    # ==================== Layer 1: PO Anchoring ====================
    
    def anchor_document_to_po(self, document_type: str, document_id: uuid.UUID) -> Optional[PurchaseOrder]:
        """
        Layer 1: Anchor an invoice or delivery note to a Purchase Order.
        Uses supplier ID and document number to find matching PO.
        """
        if document_type == "INVOICE":
            document = self.db.query(Invoice).filter(Invoice.id == document_id).first()
        elif document_type == "DELIVERY":
            document = self.db.query(DeliveryNote).filter(DeliveryNote.id == document_id).first()
        else:
            return None
        
        if not document:
            return None
        
        # Try to find matching PO by supplier_id
        # In production, this would also check PO number patterns
        matching_pos = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == document.supplier_id,
            PurchaseOrder.status == "OPEN"
        ).all()
        
        # Select the best matching PO based on amount
        if matching_pos:
            # Sort by amount proximity
            best_po = min(
                matching_pos,
                key=lambda po: abs(po.total_amount - document.total_amount)
            )
            return best_po
        
        return None
    
    # ==================== Layer 2: Cascade Matching ====================
    
    def match_invoice_to_po(self, invoice: Invoice, po: PurchaseOrder) -> Dict[str, Any]:
        """Match invoice against purchase order."""
        scores = self._calculate_match_scores(invoice, po, None)
        
        match = Match(
            match_type=MatchType.PO_INVOICE.value,
            status=MatchStatus.PENDING.value,
            confidence_score=scores["total"],
            line_score=scores["line"],
            amount_score=scores["amount"],
            date_score=scores["date"],
            purchase_order_id=po.id,
            invoice_id=invoice.id,
            po_amount=po.total_amount,
            invoice_amount=invoice.total_amount,
            variance_amount=po.total_amount - invoice.total_amount,
        )
        
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        
        # Create balance record
        self.balance_service.create_invoice_to_po_balance(invoice, po)
        
        # Decision routing
        self._route_decision(match)
        
        return self._match_to_dict(match)
    
    def match_delivery_to_po(self, delivery_note: DeliveryNote, po: PurchaseOrder) -> Dict[str, Any]:
        """Match delivery note against purchase order."""
        scores = self._calculate_match_scores(None, po, delivery_note)
        
        match = Match(
            match_type=MatchType.PO_DELIVERY.value,
            status=MatchStatus.PENDING.value,
            confidence_score=scores["total"],
            line_score=scores["line"],
            amount_score=scores["amount"],
            date_score=scores["date"],
            purchase_order_id=po.id,
            delivery_note_id=delivery_note.id,
            po_amount=po.total_amount,
            delivery_amount=delivery_note.total_amount,
            variance_amount=po.total_amount - delivery_note.total_amount,
        )
        
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        
        # Create balance record
        self.balance_service.create_delivery_to_po_balance(delivery_note, po)
        
        # Decision routing
        self._route_decision(match)
        
        return self._match_to_dict(match)
    
    def match_invoice_to_delivery(self, invoice: Invoice, delivery_note: DeliveryNote) -> Dict[str, Any]:
        """Match invoice against delivery note."""
        # Get the PO for date scoring
        po = None
        if delivery_note.purchase_order_id:
            po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == delivery_note.purchase_order_id
            ).first()
        
        scores = self._calculate_match_scores(invoice, po, delivery_note)
        
        match = Match(
            match_type=MatchType.INVOICE_DELIVERY.value,
            status=MatchStatus.PENDING.value,
            confidence_score=scores["total"],
            line_score=scores["line"],
            amount_score=scores["amount"],
            date_score=scores["date"],
            invoice_id=invoice.id,
            delivery_note_id=delivery_note.id,
            invoice_amount=invoice.total_amount,
            delivery_amount=delivery_note.total_amount,
            variance_amount=invoice.total_amount - delivery_note.total_amount,
        )
        
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        
        # Create balance record
        self.balance_service.create_invoice_to_delivery_balance(invoice, delivery_note)
        
        # Decision routing
        self._route_decision(match)
        
        return self._match_to_dict(match)
    
    def create_three_way_match(
        self,
        po: PurchaseOrder,
        invoice: Invoice,
        delivery_note: DeliveryNote
    ) -> Dict[str, Any]:
        """Create a 3-way match combining all three documents."""
        # Calculate individual scores
        po_invoice_scores = self._calculate_match_scores(invoice, po, None)
        po_delivery_scores = self._calculate_match_scores(None, po, delivery_note)
        invoice_delivery_scores = self._calculate_match_scores(invoice, po, delivery_note)
        
        # Average scores for 3-way match
        total_score = (
            po_invoice_scores["total"] + 
            po_delivery_scores["total"] + 
            invoice_delivery_scores["total"]
        ) / 3
        
        line_score = (
            po_invoice_scores["line"] + 
            po_delivery_scores["line"] + 
            invoice_delivery_scores["line"]
        ) / 3
        
        amount_score = (
            po_invoice_scores["amount"] + 
            po_delivery_scores["amount"] + 
            invoice_delivery_scores["amount"]
        ) / 3
        
        date_score = (
            po_invoice_scores["date"] + 
            po_delivery_scores["date"] + 
            invoice_delivery_scores["date"]
        ) / 3
        
        match = Match(
            match_type=MatchType.THREE_WAY.value,
            status=MatchStatus.PENDING.value,
            confidence_score=total_score,
            line_score=line_score,
            amount_score=amount_score,
            date_score=date_score,
            purchase_order_id=po.id,
            invoice_id=invoice.id,
            delivery_note_id=delivery_note.id,
            po_amount=po.total_amount,
            invoice_amount=invoice.total_amount,
            delivery_amount=delivery_note.total_amount,
            variance_amount=po.total_amount - invoice.total_amount,
        )
        
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        
        # Decision routing
        self._route_decision(match)
        
        return self._match_to_dict(match)
    
    def _calculate_match_scores(
        self,
        invoice: Optional[Invoice],
        po: Optional[PurchaseOrder],
        delivery_note: Optional[DeliveryNote]
    ) -> Dict[str, Decimal]:
        """Calculate matching scores for two documents."""
        line_score = Decimal("0.0")
        amount_score = Decimal("0.0")
        date_score = Decimal("0.0")
        
        # Line-level matching (70% weight)
        line_score = self._calculate_line_score(invoice, po, delivery_note)
        
        # Amount matching (20% weight)
        amount_score = self._calculate_amount_score(invoice, po, delivery_note)
        
        # Date matching (10% weight)
        date_score = self._calculate_date_score(invoice, po, delivery_note)
        
        # Calculate weighted total
        total = (
            line_score * Decimal(str(settings.matching_line_weight)) +
            amount_score * Decimal(str(settings.matching_amount_weight)) +
            date_score * Decimal(str(settings.matching_date_weight))
        )
        
        return {
            "total": total,
            "line": line_score,
            "amount": amount_score,
            "date": date_score,
        }
    
    def _calculate_line_score(
        self,
        invoice: Optional[Invoice],
        po: Optional[PurchaseOrder],
        delivery_note: Optional[DeliveryNote]
    ) -> Decimal:
        """Calculate line-level matching score."""
        if invoice and po:
            # Compare line items
            invoice_items = {item.item_code: item for item in invoice.line_items}
            po_items = {item.item_code: item for item in po.line_items}
            
            common_items = set(invoice_items.keys()) & set(po_items.keys())
            if not common_items:
                return Decimal("0.0")
            
            # Calculate quantity match ratio
            matched_lines = 0
            total_lines = max(len(invoice_items), len(po_items))
            
            for item_code in common_items:
                inv_qty = invoice_items[item_code].quantity
                po_qty = po_items[item_code].quantity
                if inv_qty == po_qty:
                    matched_lines += 1
                elif inv_qty <= po_qty:
                    matched_lines += 0.5
                else:
                    matched_lines += 0.25
            
            return Decimal(str(matched_lines / total_lines))
        
        elif delivery_note and po:
            # Compare line items
            dn_items = {item.item_code: item for item in delivery_note.line_items}
            po_items = {item.item_code: item for item in po.line_items}
            
            common_items = set(dn_items.keys()) & set(po_items.keys())
            if not common_items:
                return Decimal("0.0")
            
            matched_lines = 0
            total_lines = max(len(dn_items), len(po_items))
            
            for item_code in common_items:
                dn_qty = dn_items[item_code].quantity
                po_qty = po_items[item_code].quantity
                if dn_qty == po_qty:
                    matched_lines += 1
                elif dn_qty <= po_qty:
                    matched_lines += 0.5
                else:
                    matched_lines += 0.25
            
            return Decimal(str(matched_lines / total_lines))
        
        elif invoice and delivery_note:
            # Compare line items between invoice and delivery
            invoice_items = {item.item_code: item for item in invoice.line_items}
            dn_items = {item.item_code: item for item in delivery_note.line_items}
            
            common_items = set(invoice_items.keys()) & set(dn_items.keys())
            if not common_items:
                return Decimal("0.0")
            
            matched_lines = 0
            total_lines = max(len(invoice_items), len(dn_items))
            
            for item_code in common_items:
                inv_qty = invoice_items[item_code].quantity
                dn_qty = dn_items[item_code].quantity
                if inv_qty == dn_qty:
                    matched_lines += 1
                elif inv_qty <= dn_qty:
                    matched_lines += 0.75
                else:
                    matched_lines += 0.5
            
            return Decimal(str(matched_lines / total_lines))
        
        return Decimal("0.0")
    
    def _calculate_amount_score(
        self,
        invoice: Optional[Invoice],
        po: Optional[PurchaseOrder],
        delivery_note: Optional[DeliveryNote]
    ) -> Decimal:
        """Calculate amount matching score."""
        tolerance = Decimal(str(settings.amount_tolerance_percent)) / 100
        
        if invoice and po:
            diff = abs(po.total_amount - invoice.total_amount)
            max_amount = max(po.total_amount, invoice.total_amount)
            if max_amount == 0:
                return Decimal("1.0")
            variance_ratio = diff / max_amount
            if variance_ratio <= tolerance:
                return Decimal("1.0")
            return max(Decimal("0.0"), Decimal("1.0") - variance_ratio)
        
        elif delivery_note and po:
            diff = abs(po.total_amount - delivery_note.total_amount)
            max_amount = max(po.total_amount, delivery_note.total_amount)
            if max_amount == 0:
                return Decimal("1.0")
            variance_ratio = diff / max_amount
            if variance_ratio <= tolerance:
                return Decimal("1.0")
            return max(Decimal("0.0"), Decimal("1.0") - variance_ratio)
        
        elif invoice and delivery_note:
            diff = abs(invoice.total_amount - delivery_note.total_amount)
            max_amount = max(invoice.total_amount, delivery_note.total_amount)
            if max_amount == 0:
                return Decimal("1.0")
            variance_ratio = diff / max_amount
            if variance_ratio <= tolerance:
                return Decimal("1.0")
            return max(Decimal("0.0"), Decimal("1.0") - variance_ratio)
        
        return Decimal("0.0")
    
    def _calculate_date_score(
        self,
        invoice: Optional[Invoice],
        po: Optional[PurchaseOrder],
        delivery_note: Optional[DeliveryNote]
    ) -> Decimal:
        """Calculate date matching score."""
        tolerance = timedelta(days=settings.date_tolerance_days)
        
        if invoice and po:
            diff = abs((invoice.invoice_date - po.order_date).days)
            if diff <= tolerance.days:
                return Decimal("1.0")
            return max(Decimal("0.0"), Decimal(str(1 - diff / (tolerance.days * 2))))
        
        elif delivery_note and po:
            if po.expected_delivery_date:
                diff = abs((delivery_note.delivery_date - po.expected_delivery_date).days)
                if diff <= tolerance.days:
                    return Decimal("1.0")
                return max(Decimal("0.0"), Decimal(str(1 - diff / (tolerance.days * 2))))
            else:
                diff = abs((delivery_note.delivery_date - po.order_date).days)
                if diff <= 30:  # Default 30 days
                    return Decimal("1.0")
                return Decimal("0.5")
        
        elif invoice and delivery_note:
            diff = abs((invoice.invoice_date - delivery_note.delivery_date).days)
            if diff <= tolerance.days:
                return Decimal("1.0")
            return max(Decimal("0.0"), Decimal(str(1 - diff / (tolerance.days * 2))))
        
        return Decimal("0.0")
    
    # ==================== Layer 3: Decision Routing ====================
    
    def _route_decision(self, match: Match) -> None:
        """Route match through decision engine."""
        threshold = Decimal(str(settings.auto_approve_threshold))
        
        if match.confidence_score >= threshold and match.variance_amount == Decimal("0"):
            match.status = MatchStatus.CONFIRMED.value
            match.decision = "AUTO_APPROVE"
            match.auto_approved = True
        elif match.confidence_score >= threshold:
            match.status = MatchStatus.CONFIRMED.value
            match.decision = "HUMAN_REVIEW"  # Variance needs manual review
        else:
            match.status = MatchStatus.PENDING.value
            match.decision = "HUMAN_REVIEW"
        
        self.db.commit()
    
    # ==================== Match Operations ====================
    
    def get_match_by_id(self, match_id: uuid.UUID) -> Optional[Match]:
        """Get match by ID."""
        return self.db.query(Match).options(
            joinedload(Match.purchase_order),
            joinedload(Match.invoice),
            joinedload(Match.delivery_note),
            joinedload(Match.reviewed_by_user),
        ).filter(Match.id == match_id).first()
    
    def get_matches(
        self,
        status: Optional[str] = None,
        match_type: Optional[str] = None,
        purchase_order_id: Optional[uuid.UUID] = None,
        invoice_id: Optional[uuid.UUID] = None,
        delivery_note_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Match], int]:
        """Get matches with filters."""
        query = self.db.query(Match).options(
            joinedload(Match.purchase_order),
            joinedload(Match.invoice),
            joinedload(Match.delivery_note),
        )
        
        if status:
            query = query.filter(Match.status == status)
        if match_type:
            query = query.filter(Match.match_type == match_type)
        if purchase_order_id:
            query = query.filter(Match.purchase_order_id == purchase_order_id)
        if invoice_id:
            query = query.filter(Match.invoice_id == invoice_id)
        if delivery_note_id:
            query = query.filter(Match.delivery_note_id == delivery_note_id)
        
        total = query.count()
        matches = query.order_by(Match.created_at.desc()).offset(skip).limit(limit).all()
        
        return matches, total
    
    def review_match(
        self,
        match_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        status: str,
        review_notes: Optional[str] = None,
    ) -> Optional[Match]:
        """Review and update match status."""
        match = self.get_match_by_id(match_id)
        if not match:
            return None
        
        match.status = status
        match.reviewed_by = reviewer_id
        match.reviewed_at = datetime.utcnow()
        if review_notes:
            match.review_notes = review_notes
        
        # Set decision based on status
        if status == MatchStatus.CONFIRMED.value:
            match.decision = "APPROVED"
            match.auto_approved = False
        elif status == MatchStatus.REJECTED.value:
            match.decision = "DISPUTE"
            match.auto_approved = False
        
        self.db.commit()
        self.db.refresh(match)
        
        # Learning loop: Update future matching with human confirmation
        self._update_learning_data(match)
        
        return match
    
    def _update_learning_data(self, match: Match) -> None:
        """Update learning data from human confirmations."""
        # In a production system, this would update ML models or rules engine
        # For now, we just log the confirmation
        pass
    
    def get_pending_matches(self, limit: int = 50) -> List[Match]:
        """Get all pending matches for review."""
        matches, _ = self.get_matches(status=MatchStatus.PENDING.value, limit=limit)
        return matches
    
    def get_match_summary(self) -> Dict[str, Any]:
        """Get summary statistics of matches."""
        total = self.db.query(Match).count()
        pending = self.db.query(Match).filter(Match.status == MatchStatus.PENDING.value).count()
        confirmed = self.db.query(Match).filter(Match.status == MatchStatus.CONFIRMED.value).count()
        rejected = self.db.query(Match).filter(Match.status == MatchStatus.REJECTED.value).count()
        
        auto_approved = self.db.query(Match).filter(Match.auto_approved == True).count()
        
        return {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "rejected": rejected,
            "auto_approved": auto_approved,
            "pending_percentage": (pending / total * 100) if total > 0 else 0,
        }
    
    def _match_to_dict(self, match: Match) -> Dict[str, Any]:
        """Convert match to dictionary."""
        return {
            "id": str(match.id),
            "match_type": match.match_type,
            "status": match.status,
            "confidence_score": float(match.confidence_score),
            "line_score": float(match.line_score),
            "amount_score": float(match.amount_score),
            "date_score": float(match.date_score),
            "purchase_order_id": str(match.purchase_order_id) if match.purchase_order_id else None,
            "invoice_id": str(match.invoice_id) if match.invoice_id else None,
            "delivery_note_id": str(match.delivery_note_id) if match.delivery_note_id else None,
            "po_amount": float(match.po_amount) if match.po_amount else None,
            "invoice_amount": float(match.invoice_amount) if match.invoice_amount else None,
            "delivery_amount": float(match.delivery_amount) if match.delivery_amount else None,
            "variance_amount": float(match.variance_amount) if match.variance_amount else None,
            "decision": match.decision,
            "auto_approved": match.auto_approved,
            "created_at": match.created_at.isoformat(),
        }
