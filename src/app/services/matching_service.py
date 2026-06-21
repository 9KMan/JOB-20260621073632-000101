// src/app/services/matching_service.py
"""Matching service for 3-way matching operations."""

from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session

from src.app.config import get_settings
from src.app.models import (
    Invoice, InvoiceLine,
    DeliveryNote, DeliveryNoteLine,
    PurchaseOrder, PurchaseOrderLine,
    MatchResult, MatchDecision, HumanConfirmation,
    BalanceLedger, BalanceType
)
from src.app.engine.layer1_anchor import Layer1Anchor
from src.app.engine.layer2_cascade import Layer2Cascade
from src.app.engine.layer3_balance import Layer3Balance
from src.app.engine.decision_router import DecisionRouter

settings = get_settings()


class MatchingService:
    """Service for performing 3-way matching operations."""

    def __init__(self):
        """Initialize matching service with engine components."""
        self.layer1 = Layer1Anchor()
        self.layer2 = Layer2Cascade()
        self.layer3 = Layer3Balance()
        self.decision_router = DecisionRouter()

    def match_invoice_to_po(
        self,
        db: Session,
        invoice_id: str,
        po_id: Optional[str] = None
    ) -> Optional[MatchResult]:
        """Match an invoice against a purchase order."""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return None

        # Layer 1: Anchor to PO
        anchor_po = po_id
        if not anchor_po:
            anchor_po = self.layer1.find_anchor_po(
                db,
                invoice.supplier_id,
                invoice.po_reference,
                invoice.invoice_number
            )

        if not anchor_po:
            return self._create_unmatched_result(
                db, invoice, None, None, "INVOICE_PO",
                "No matching purchase order found"
            )

        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == anchor_po).first()
        if not po:
            return None

        # Layer 2: Cascade matching
        match_score, scores, variance = self.layer2.match_invoice_po(invoice, po)

        # Layer 3: Balance resolution
        balance_info = self.layer3.check_balance(db, invoice, po, "INVOICE_PO")

        # Decision routing
        decision = self.decision_router.route(match_score, "INVOICE_PO")

        # Create match result
        match_result = MatchResult(
            invoice_id=invoice_id,
            purchase_order_id=po.id,
            match_type="INVOICE_PO",
            match_score=Decimal(str(match_score)),
            line_level_score=Decimal(str(scores.get("line_level", 0))),
            amount_score=Decimal(str(scores.get("amount", 0))),
            date_score=Decimal(str(scores.get("date", 0))),
            decision=decision.value,
            auto_processed="TRUE" if decision != MatchDecision.PENDING else "FALSE",
            invoice_amount=invoice.total_amount,
            po_amount=po.total_amount,
            variance_amount=Decimal(str(variance.get("amount", 0))),
            invoice_quantity=sum(line.quantity for line in invoice.lines),
            po_quantity=sum(line.quantity for line in po.lines),
            variance_quantity=Decimal(str(variance.get("quantity", 0))),
            details=self._format_match_details(scores, variance),
            discrepancy_notes=self._format_discrepancy_notes(variance)
        )

        db.add(match_result)
        db.commit()
        db.refresh(match_result)

        # Update balance ledger if partial match
        if decision == MatchDecision.CONFIRMED:
            self.layer3.update_balance_ledger(
                db, match_result, invoice, po, None, balance_info
            )

        return match_result

    def match_delivery_note_to_po(
        self,
        db: Session,
        delivery_note_id: str,
        po_id: Optional[str] = None
    ) -> Optional[MatchResult]:
        """Match a delivery note against a purchase order."""
        dn = db.query(DeliveryNote).filter(DeliveryNote.id == delivery_note_id).first()
        if not dn:
            return None

        # Layer 1: Anchor to PO
        anchor_po = po_id
        if not anchor_po:
            anchor_po = self.layer1.find_anchor_po(
                db,
                dn.supplier_id,
                dn.po_reference,
                dn.dn_number
            )

        if not anchor_po:
            return self._create_unmatched_result(
                db, None, delivery_note_id, None, "DELIVERY_NOTE_PO",
                "No matching purchase order found"
            )

        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == anchor_po).first()
        if not po:
            return None

        # Layer 2: Cascade matching
        match_score, scores, variance = self.layer2.match_dn_po(dn, po)

        # Layer 3: Balance resolution
        balance_info = self.layer3.check_balance(db, None, po, "DELIVERY_NOTE_PO", dn)

        # Decision routing
        decision = self.decision_router.route(match_score, "DELIVERY_NOTE_PO")

        # Create match result
        match_result = MatchResult(
            delivery_note_id=delivery_note_id,
            purchase_order_id=po.id,
            match_type="DELIVERY_NOTE_PO",
            match_score=Decimal(str(match_score)),
            line_level_score=Decimal(str(scores.get("line_level", 0))),
            amount_score=Decimal(str(scores.get("amount", 0))),
            date_score=Decimal(str(scores.get("date", 0))),
            decision=decision.value,
            auto_processed="TRUE" if decision != MatchDecision.PENDING else "FALSE",
            dn_amount=dn.total_amount,
            po_amount=po.total_amount,
            variance_amount=Decimal(str(variance.get("amount", 0))),
            dn_quantity=sum(line.quantity for line in dn.lines),
            po_quantity=sum(line.quantity for line in po.lines),
            variance_quantity=Decimal(str(variance.get("quantity", 0))),
            details=self._format_match_details(scores, variance),
            discrepancy_notes=self._format_discrepancy_notes(variance)
        )

        db.add(match_result)
        db.commit()
        db.refresh(match_result)

        # Update balance ledger if partial match
        if decision == MatchDecision.CONFIRMED:
            self.layer3.update_balance_ledger(
                db, match_result, None, po, dn, balance_info
            )

        return match_result

    def match_three_way(
        self,
        db: Session,
        invoice_id: str,
        delivery_note_id: Optional[str] = None,
        po_id: Optional[str] = None
    ) -> Optional[MatchResult]:
        """Perform full 3-way matching."""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return None

        # Layer 1: Anchor to PO
        anchor_po = po_id
        if not anchor_po:
            anchor_po = self.layer1.find_anchor_po(
                db,
                invoice.supplier_id,
                invoice.po_reference,
                invoice.invoice_number
            )

        if not anchor_po:
            return None

        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == anchor_po).first()
        if not po:
            return None

        # Find delivery note if not provided
        if not delivery_note_id:
            delivery_note_id = self._find_matching_dn(
                db, invoice.supplier_id, po.id
            )

        dn = None
        if delivery_note_id:
            dn = db.query(DeliveryNote).filter(
                DeliveryNote.id == delivery_note_id
            ).first()

        # Layer 2: Three-way matching
        match_score, scores, variance = self.layer2.match_three_way(invoice, dn, po)

        # Layer 3: Balance resolution
        balance_info = self.layer3.check_balance(db, invoice, po, "THREE_WAY", dn)

        # Decision routing
        decision = self.decision_router.route(match_score, "THREE_WAY")

        # Create match result
        match_result = MatchResult(
            invoice_id=invoice_id,
            delivery_note_id=delivery_note_id,
            purchase_order_id=po.id,
            match_type="THREE_WAY",
            match_score=Decimal(str(match_score)),
            line_level_score=Decimal(str(scores.get("line_level", 0))),
            amount_score=Decimal(str(scores.get("amount", 0))),
            date_score=Decimal(str(scores.get("date", 0))),
            decision=decision.value,
            auto_processed="TRUE" if decision != MatchDecision.PENDING else "FALSE",
            invoice_amount=invoice.total_amount,
            po_amount=po.total_amount,
            dn_amount=dn.total_amount if dn else None,
            variance_amount=Decimal(str(variance.get("amount", 0))),
            details=self._format_match_details(scores, variance),
            discrepancy_notes=self._format_discrepancy_notes(variance)
        )

        db.add(match_result)
        db.commit()
        db.refresh(match_result)

        # Update balance ledger
        if decision == MatchDecision.CONFIRMED:
            self.layer3.update_balance_ledger(
                db, match_result, invoice, po, dn, balance_info
            )

        return match_result

    def confirm_match(
        self,
        db: Session,
        match_result_id: str,
        confirmation: HumanConfirmation
    ) -> Optional[MatchResult]:
        """Apply human confirmation to a match result."""
        match_result = db.query(MatchResult).filter(
            MatchResult.id == match_result_id
        ).first()

        if not match_result:
            return None

        # Add confirmation
        confirmation.match_result_id = match_result_id
        db.add(confirmation)

        # Update decision
        match_result.decision = confirmation.new_decision
        match_result.auto_processed = "FALSE"

        # Apply confidence boost for future matching
        if confirmation.confidence_boost:
            self._apply_learning_boost(db, match_result, confirmation.confidence_boost)

        db.commit()
        db.refresh(match_result)

        return match_result

    def get_match_summary(self, db: Session) -> dict:
        """Get summary of all matches."""
        total = db.query(MatchResult).filter(MatchResult.is_deleted == False).count()  # noqa: E712
        
        confirmed = db.query(MatchResult).filter(
            MatchResult.is_deleted == False,  # noqa: E712
            MatchResult.decision == MatchDecision.CONFIRMED.value
        ).count()

        pending = db.query(MatchResult).filter(
            MatchResult.is_deleted == False,  # noqa: E712
            MatchResult.decision == MatchDecision.PENDING.value
        ).count()

        rejected = db.query(MatchResult).filter(
            MatchResult.is_deleted == False,  # noqa: E712
            MatchResult.decision == MatchDecision.REJECTED.value
        ).count()

        auto_approved = db.query(MatchResult).filter(
            MatchResult.is_deleted == False,  # noqa: E712
            MatchResult.decision == MatchDecision.CONFIRMED.value,
            MatchResult.auto_processed == "TRUE"
        ).count()

        human_review = confirmed - auto_approved

        return {
            "total_matches": total,
            "confirmed": confirmed,
            "pending": pending,
            "rejected": rejected,
            "auto_approved": auto_approved,
            "human_review": human_review
        }

    def _find_matching_dn(
        self,
        db: Session,
        supplier_id: str,
        po_id: str
    ) -> Optional[str]:
        """Find matching delivery note for given supplier and PO."""
        dn = db.query(DeliveryNote).filter(
            DeliveryNote.supplier_id == supplier_id,
            DeliveryNote.po_reference == db.query(PurchaseOrder.po_number).filter(
                PurchaseOrder.id == po_id
            ).scalar_subquery(),
            DeliveryNote.is_deleted == False  # noqa: E712
        ).first()

        return dn.id if dn else None

    def _create_unmatched_result(
        self,
        db: Session,
        invoice: Optional[Invoice],
        delivery_note: Optional[DeliveryNote],
        po: Optional[PurchaseOrder],
        match_type: str,
        notes: str
    ) -> MatchResult:
        """Create a rejected match result for unmatched documents."""
        match_result = MatchResult(
            invoice_id=invoice.id if invoice else None,
            delivery_note_id=delivery_note.id if delivery_note else None,
            purchase_order_id=po.id if po else None,
            match_type=match_type,
            match_score=Decimal("0"),
            decision=MatchDecision.REJECTED.value,
            auto_processed="TRUE",
            discrepancy_notes=notes
        )
        db.add(match_result)
        db.commit()
        db.refresh(match_result)
        return match_result

    def _format_match_details(self, scores: dict, variance: dict) -> str:
        """Format match details as string."""
        details = []
        details.append(f"Line Level Score: {scores.get('line_level', 0):.2%}")
        details.append(f"Amount Score: {scores.get('amount', 0):.2%}")
        details.append(f"Date Score: {scores.get('date', 0):.2%}")
        return "; ".join(details)

    def _format_discrepancy_notes(self, variance: dict) -> str:
        """Format discrepancy notes from variance data."""
        notes = []
        if variance.get("amount", 0) != 0:
            notes.append(f"Amount variance: {variance['amount']}")
        if variance.get("quantity", 0) != 0:
            notes.append(f"Quantity variance: {variance['quantity']}")
        if variance.get("date_days", 0) > 0:
            notes.append(f"Date variance: {variance['date_days']} days")
        return "; ".join(notes) if notes else "No discrepancies"

    def _apply_learning_boost(
        self,
        db: Session,
        match_result: MatchResult,
        boost: Decimal
    ) -> None:
        """Apply confidence boost from human confirmation to learning system."""
        # Store confirmation for future matching improvements
        # This data can be used to adjust weights in future matching operations
        pass
