// src/app/services/matching_service.py
"""Matching service - Orchestrates the 3-layer matching process."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models import (
    Invoice,
    InvoiceLine,
    DeliveryNote,
    DeliveryNoteLine,
    PurchaseOrder,
    POLine,
    Match,
    MatchLine,
    MatchStatus,
    MatchResult,
)
from app.services.layer1_anchor import Layer1AnchorService
from app.services.layer2_cascade import Layer2CascadeService
from app.services.layer3_balance import Layer3BalanceService
from app.services.decision_engine import DecisionEngine


class MatchingService:
    """Service for orchestrating the 3-way matching process."""

    def __init__(self, db: Session):
        """Initialize matching service."""
        self.db = db
        self.layer1 = Layer1AnchorService(db)
        self.layer2 = Layer2CascadeService(db)
        self.layer3 = Layer3BalanceService(db)
        self.decision_engine = DecisionEngine(db)

    def match_invoice_to_po(
        self,
        invoice_id: UUID,
        po_id: UUID | None = None,
    ) -> Match | None:
        """
        Match an invoice against purchase orders.
        
        Layer 1: Anchor to PO if not specified
        Layer 2: Cascade matching with scoring
        Layer 3: Balance resolution
        Decision: Route to appropriate status
        """
        invoice = self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            return None

        # Layer 1: Anchor to PO
        if po_id:
            po = self.db.query(PurchaseOrder).options(
                joinedload(PurchaseOrder.lines)
            ).filter(PurchaseOrder.id == po_id).first()
        else:
            po = self.layer1.find_anchor_po(
                supplier_id=invoice.supplier_id,
                po_reference=invoice.po_reference,
            )

        if not po:
            return None

        # Layer 2: Cascade matching
        match_result = self.layer2.match_invoice_to_po(invoice, po)

        if not match_result:
            return None

        # Create match record
        match = self._create_match_record(
            invoice=invoice,
            po=po,
            match_type="invoice_po",
            scoring=match_result["scoring"],
            lines=match_result["lines"],
        )

        # Layer 3: Balance resolution
        self.layer3.update_balances(match, invoice, po)

        # Decision routing
        match = self.decision_engine.route_decision(match)

        return match

    def match_delivery_note_to_po(
        self,
        dn_id: UUID,
        po_id: UUID | None = None,
    ) -> Match | None:
        """
        Match a delivery note against purchase orders.
        
        Layer 1: Anchor to PO if not specified
        Layer 2: Cascade matching with scoring
        Layer 3: Balance resolution
        Decision: Route to appropriate status
        """
        dn = self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.lines)
        ).filter(DeliveryNote.id == dn_id).first()
        
        if not dn:
            return None

        # Layer 1: Anchor to PO
        if po_id:
            po = self.db.query(PurchaseOrder).options(
                joinedload(PurchaseOrder.lines)
            ).filter(PurchaseOrder.id == po_id).first()
        else:
            po = self.layer1.find_anchor_po(
                supplier_id=dn.supplier_id,
                po_reference=dn.po_reference,
            )

        if not po:
            return None

        # Layer 2: Cascade matching
        match_result = self.layer2.match_dn_to_po(dn, po)

        if not match_result:
            return None

        # Create match record
        match = self._create_match_record(
            dn=dn,
            po=po,
            match_type="dn_po",
            scoring=match_result["scoring"],
            lines=match_result["lines"],
        )

        # Layer 3: Balance resolution
        self.layer3.update_dn_balances(match, dn, po)

        # Decision routing
        match = self.decision_engine.route_decision(match)

        return match

    def match_invoice_to_delivery_note(
        self,
        invoice_id: UUID,
        dn_id: UUID,
    ) -> Match | None:
        """
        Match an invoice against a delivery note.
        
        Layer 2: Direct cascade matching
        Decision: Route to appropriate status
        """
        invoice = self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(Invoice.id == invoice_id).first()
        
        dn = self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.lines)
        ).filter(DeliveryNote.id == dn_id).first()
        
        if not invoice or not dn:
            return None

        # Layer 2: Cascade matching
        match_result = self.layer2.match_invoice_to_dn(invoice, dn)

        if not match_result:
            return None

        # Create match record
        match = self._create_match_record(
            invoice=invoice,
            dn=dn,
            match_type="invoice_dn",
            scoring=match_result["scoring"],
            lines=match_result["lines"],
        )

        # Decision routing
        match = self.decision_engine.route_decision(match)

        return match

    def perform_three_way_match(
        self,
        invoice_id: UUID,
        dn_id: UUID,
        po_id: UUID | None = None,
    ) -> Match | None:
        """
        Perform complete 3-way matching.
        
        Matches Invoice ↔ Delivery Note ↔ Purchase Order
        """
        invoice = self.db.query(Invoice).options(
            joinedload(Invoice.lines)
        ).filter(Invoice.id == invoice_id).first()
        
        dn = self.db.query(DeliveryNote).options(
            joinedload(DeliveryNote.lines)
        ).filter(DeliveryNote.id == dn_id).first()
        
        if not invoice or not dn:
            return None

        # Layer 1: Find anchor PO
        if po_id:
            po = self.db.query(PurchaseOrder).options(
                joinedload(PurchaseOrder.lines)
            ).filter(PurchaseOrder.id == po_id).first()
        else:
            po = self.layer1.find_anchor_po(
                supplier_id=invoice.supplier_id,
                po_reference=invoice.po_reference or dn.po_reference,
            )

        # Layer 2: Three-way matching
        match_result = self.layer2.perform_three_way_match(invoice, dn, po)

        if not match_result:
            return None

        # Create match record
        match = self._create_match_record(
            invoice=invoice,
            dn=dn,
            po=po,
            match_type="three_way",
            scoring=match_result["scoring"],
            lines=match_result["lines"],
        )

        # Layer 3: Balance resolution for all documents
        if po:
            self.layer3.update_balances(match, invoice, po)
            self.layer3.update_dn_balances(match, dn, po)

        # Decision routing
        match = self.decision_engine.route_decision(match)

        return match

    def _create_match_record(
        self,
        invoice: Invoice | None = None,
        dn: DeliveryNote | None = None,
        po: PurchaseOrder | None = None,
        match_type: str = "",
        scoring: dict[str, Decimal] | None = None,
        lines: list[dict[str, Any]] | None = None,
    ) -> Match:
        """Create a match record with line items."""
        scoring = scoring or {}
        lines = lines or []

        match = Match(
            invoice_id=invoice.id if invoice else None,
            dn_id=dn.id if dn else None,
            po_id=po.id if po else None,
            match_type=match_type,
            status=MatchStatus.PENDING,
            result=MatchResult.PARTIAL_MATCH
            if scoring.get("overall_score", 0) < 100
            else MatchResult.FULL_MATCH,
            overall_score=scoring.get("overall_score", Decimal("0.00")),
            line_level_score=scoring.get("line_level_score", Decimal("0.00")),
            amount_score=scoring.get("amount_score", Decimal("0.00")),
            date_score=scoring.get("date_score", Decimal("0.00")),
            invoice_amount=invoice.total_amount if invoice else None,
            dn_amount=dn.total_amount if dn else None,
            po_amount=po.total_amount if po else None,
            variance_amount=scoring.get("variance_amount", Decimal("0.00")),
            match_date=date.today(),
            scoring_details={
                "line_matches": len([l for l in lines if l.get("score", 0) >= 70]),
                "total_lines": len(lines),
            },
        )

        self.db.add(match)
        self.db.flush()

        # Create line matches
        for line_data in lines:
            match_line = MatchLine(
                match_id=match.id,
                invoice_line_id=line_data.get("invoice_line_id"),
                dn_line_id=line_data.get("dn_line_id"),
                po_line_id=line_data.get("po_line_id"),
                match_type=line_data.get("match_type", match_type),
                score=line_data.get("score", Decimal("0.00")),
                quantity_match=line_data.get("quantity_match", False),
                price_match=line_data.get("price_match", False),
                product_match=line_data.get("product_match", False),
                invoice_quantity=line_data.get("invoice_quantity"),
                dn_quantity=line_data.get("dn_quantity"),
                po_quantity=line_data.get("po_quantity"),
                matched_quantity=line_data.get("matched_quantity", Decimal("0.00")),
                invoice_amount=line_data.get("invoice_amount"),
                po_amount=line_data.get("po_amount"),
                variance_quantity=line_data.get("variance_quantity", Decimal("0.00")),
                variance_amount=line_data.get("variance_amount", Decimal("0.00")),
            )
            self.db.add(match_line)

        self.db.commit()
        self.db.refresh(match)

        return match

    def confirm_match(self, match_id: UUID, notes: str | None = None) -> Match | None:
        """Confirm a pending match."""
        return self.decision_engine.confirm_match(match_id, notes)

    def reject_match(self, match_id: UUID, notes: str | None = None) -> Match | None:
        """Reject a pending match."""
        return self.decision_engine.reject_match(match_id, notes)
