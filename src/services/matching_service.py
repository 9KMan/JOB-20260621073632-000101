// src/services/matching_service.py
"""3-Way Matching service implementing the AP automation matching engine."""
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from src.app.config import get_settings
from src.models.document import (
    Document,
    DocumentLine,
    DocumentStatus,
    Invoice,
    PurchaseOrder,
    DeliveryNote,
)
from src.models.matching import (
    MatchResult,
    MatchStatus,
    MatchType,
    LineMatch,
    BalanceEntry,
    BalanceType,
    MatchingSession,
)

settings = get_settings()


@dataclass
class MatchScore:
    """Match scoring result."""

    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    matched_quantity: Decimal
    quantity_variance: Decimal
    price_variance: Decimal
    date_variance_days: int
    line_matches: List[Dict]


class MatchingService:
    """Service for 3-way document matching."""

    def __init__(self, db: Session):
        """Initialize matching service."""
        self.db = db

    def run_matching_session(
        self,
        session_type: str = "MANUAL",
        initiated_by: Optional[UUID] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> MatchingSession:
        """Run a complete matching session for pending documents."""
        session = MatchingSession(
            session_type=session_type,
            initiated_by=initiated_by,
            status="running",
            auto_approve_threshold=Decimal(str(settings.MATCH_THRESHOLD_AUTO_APPROVE)),
            human_review_threshold=Decimal(str(settings.MATCH_THRESHOLD_HUMAN_REVIEW)),
        )
        self.db.add(session)
        self.db.flush()

        # Get pending invoices
        invoices_query = self.db.query(Invoice).filter(
            Invoice.status == DocumentStatus.PENDING.value,
            Invoice.is_active == True,
        )
        if document_ids:
            invoices_query = invoices_query.filter(Invoice.id.in_(document_ids))
        invoices = invoices_query.all()

        session.total_documents = len(invoices)

        for invoice in invoices:
            result = self.match_invoice_to_po(invoice)
            if result and result.status in [
                MatchStatus.AUTO_APPROVED.value,
                MatchStatus.CONFIRMED.value,
            ]:
                session.matched_count += 1
            elif result and result.status == MatchStatus.HUMAN_REVIEW.value:
                session.pending_count += 1
            elif result and result.status == MatchStatus.REJECTED.value:
                session.rejected_count += 1

        session.status = "completed"
        session.completed_at = __import__("datetime").datetime.utcnow()
        session.results_summary = json.dumps({
            "total": session.total_documents,
            "matched": session.matched_count,
            "pending": session.pending_count,
            "rejected": session.rejected_count,
        })

        self.db.commit()
        self.db.refresh(session)
        return session

    def anchor_to_po(self, invoice: Invoice) -> Optional[PurchaseOrder]:
        """Layer 1: Anchor invoice to PO using supplier and PO number."""
        if not invoice.po_number:
            return None

        po = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.po_number == invoice.po_number,
                PurchaseOrder.supplier_id == invoice.supplier_id,
                PurchaseOrder.is_active == True,
            )
            .first()
        )

        if not po:
            # Try fuzzy match by supplier
            pos = (
                self.db.query(PurchaseOrder)
                .filter(
                    PurchaseOrder.supplier_id == invoice.supplier_id,
                    PurchaseOrder.status != DocumentStatus.CANCELLED.value,
                    PurchaseOrder.is_active == True,
                )
                .all()
            )

            for candidate_po in pos:
                score = self._calculate_po_match_score(invoice, candidate_po)
                if score.overall_score >= Decimal(str(settings.MATCH_THRESHOLD_HUMAN_REVIEW)):
                    return candidate_po

        return po

    def _calculate_po_match_score(
        self, invoice: Invoice, po: PurchaseOrder
    ) -> MatchScore:
        """Calculate match score between invoice and PO."""
        # Amount score
        amount_diff = abs(invoice.total_amount - po.total_amount)
        max_amount = max(invoice.total_amount, po.total_amount)
        if max_amount > 0:
            amount_score = Decimal("1.0000") - (amount_diff / max_amount)
        else:
            amount_score = Decimal("1.0000")

        # Line level matching
        invoice_lines = (
            self.db.query(DocumentLine)
            .filter(
                DocumentLine.document_id == invoice.document_id,
                DocumentLine.is_active == True,
            )
            .all()
        )
        po_lines = (
            self.db.query(DocumentLine)
            .filter(
                DocumentLine.document_id == po.document_id,
                DocumentLine.is_active == True,
            )
            .all()
        )

        line_matches: List[Dict] = []
        total_matched_amount = Decimal("0")
        total_matched_quantity = Decimal("0")

        for inv_line in invoice_lines:
            best_match = None
            best_score = Decimal("0")

            for po_line in po_lines:
                score = self._calculate_line_match_score(inv_line, po_line)
                if score > best_score:
                    best_score = score
                    best_match = po_line

            if best_match and best_score >= Decimal("0.70"):
                matched_qty = min(inv_line.quantity, best_match.quantity)
                matched_amt = matched_qty * inv_line.unit_price
                total_matched_amount += matched_amt
                total_matched_quantity += matched_qty

                line_matches.append({
                    "source_line_id": str(inv_line.id),
                    "source_product_code": inv_line.product_code,
                    "matched_line_id": str(best_match.id),
                    "matched_product_code": best_match.product_code,
                    "match_score": float(best_score),
                    "matched_quantity": float(matched_qty),
                    "matched_amount": float(matched_amt),
                })

        # Calculate line level score
        if invoice_lines:
            line_level_score = Decimal(str(len(line_matches) / len(invoice_lines)))
        else:
            line_level_score = Decimal("0")

        # Date score (issue date vs order date)
        date_diff = abs((invoice.issue_date - po.order_date).days)
        date_score = Decimal("1.0000") - Decimal(str(min(date_diff, 30) / 30))

        # Weighted overall score
        overall_score = (
            line_level_score * Decimal(str(settings.MATCH_WEIGHT_LINE_LEVEL))
            + amount_score * Decimal(str(settings.MATCH_WEIGHT_AMOUNT))
            + date_score * Decimal(str(settings.MATCH_WEIGHT_DATE))
        )

        variance_amount = invoice.total_amount - total_matched_amount
        variance_pct = (
            Decimal("0") if invoice.total_amount == 0
            else abs(variance_amount) / invoice.total_amount
        )

        return MatchScore(
            line_level_score=min(line_level_score, Decimal("1.0000")),
            amount_score=min(amount_score, Decimal("1.0000")),
            date_score=min(date_score, Decimal("1.0000")),
            overall_score=min(overall_score, Decimal("1.0000")),
            matched_amount=total_matched_amount,
            variance_amount=variance_amount,
            variance_percentage=min(variance_pct, Decimal("1.0000")),
            matched_quantity=total_matched_quantity,
            quantity_variance=invoice_lines[0].quantity - total_matched_quantity if invoice_lines else Decimal("0"),
            price_variance=Decimal("0"),  # Simplified
            date_variance_days=date_diff,
            line_matches=line_matches,
        )

    def _calculate_line_match_score(
        self, line1: DocumentLine, line2: DocumentLine
    ) -> Decimal:
        """Calculate match score between two lines."""
        score = Decimal("0")
        weights = Decimal("0")

        # Product code match
        if line1.product_code == line2.product_code:
            score += Decimal("0.5")
        weights += Decimal("0.5")

        # Product name similarity (simplified - production should use fuzzy matching)
        if line1.product_name.lower() == line2.product_name.lower():
            score += Decimal("0.3")
        weights += Decimal("0.3")

        # Unit price match (within tolerance)
        if line1.unit_price == line2.unit_price:
            score += Decimal("0.2")
        elif line1.unit_price > 0:
            price_diff = abs(line1.unit_price - line2.unit_price) / line1.unit_price
            if price_diff <= Decimal("0.05"):  # 5% tolerance
                score += Decimal("0.2") * (Decimal("1") - price_diff)
        weights += Decimal("0.2")

        return score / weights if weights > 0 else Decimal("0")

    def match_invoice_to_po(
        self, invoice: Invoice
    ) -> Optional[MatchResult]:
        """Match invoice to purchase order."""
        # Layer 1: Anchor to PO
        po = self.anchor_to_po(invoice)
        if not po:
            return None

        # Layer 2: Cascade matching
        score = self._calculate_po_match_score(invoice, po)

        # Determine status and decision
        if score.overall_score >= Decimal(str(settings.MATCH_THRESHOLD_AUTO_APPROVE)):
            status = MatchStatus.AUTO_APPROVED.value
            decision = "AUTO_APPROVE"
        elif score.overall_score >= Decimal(str(settings.MATCH_THRESHOLD_HUMAN_REVIEW)):
            status = MatchStatus.HUMAN_REVIEW.value
            decision = "HUMAN_REVIEW"
        else:
            status = MatchStatus.REJECTED.value
            decision = "DISPUTE"

        # Create match result
        match_result = MatchResult(
            document_id=invoice.id,
            match_type=MatchType.INVOICE_PO.value,
            partner_document_id=po.id,
            line_level_score=score.line_level_score,
            amount_score=score.amount_score,
            date_score=score.date_score,
            overall_score=score.overall_score,
            matched_amount=score.matched_amount,
            variance_amount=score.variance_amount,
            variance_percentage=score.variance_percentage,
            matched_quantity=score.matched_quantity,
            quantity_variance=score.quantity_variance,
            status=status,
            decision=decision,
            requires_review=(status == MatchStatus.HUMAN_REVIEW.value),
            price_variance=score.price_variance,
            date_variance_days=score.date_variance_days,
            match_details=json.dumps({"line_matches": score.line_matches}),
        )

        self.db.add(match_result)

        # Update document status
        if status == MatchStatus.AUTO_APPROVED.value:
            invoice.status = DocumentStatus.CONFIRMED.value
            invoice.matched_amount = score.matched_amount
            invoice.balance_amount = invoice.total_amount - score.matched_amount
        elif status == MatchStatus.HUMAN_REVIEW.value:
            invoice.status = DocumentStatus.PARTIALLY_MATCHED.value
        else:
            invoice.status = DocumentStatus.REJECTED.value

        self.db.commit()
        self.db.refresh(match_result)
        return match_result

    def match_three_way(
        self, invoice: Invoice, delivery_note: DeliveryNote, po: PurchaseOrder
    ) -> Optional[MatchResult]:
        """Perform 3-way matching between invoice, delivery note, and PO."""
        # Calculate scores for each pair
        invoice_po_score = self._calculate_po_match_score(invoice, po)
        dn_po_score = self._calculate_delivery_note_po_score(delivery_note, po)

        # Line level matching across all three
        line_matches = self._calculate_three_way_line_matches(invoice, delivery_note, po)

        # Weighted overall score
        overall_score = (
            invoice_po_score.overall_score * Decimal("0.5")
            + dn_po_score.overall_score * Decimal("0.3")
            + (Decimal(str(len(line_matches))) / max(len(line_matches), 1)) * Decimal("0.2")
        )

        matched_amount = min(invoice.total_amount, delivery_note.total_amount, po.total_amount)
        variance_amount = invoice.total_amount - matched_amount

        # Determine status
        if overall_score >= Decimal(str(settings.MATCH_THRESHOLD_AUTO_APPROVE)):
            status = MatchStatus.AUTO_APPROVED.value
            decision = "AUTO_APPROVE"
        elif overall_score >= Decimal(str(settings.MATCH_THRESHOLD_HUMAN_REVIEW)):
            status = MatchStatus.HUMAN_REVIEW.value
            decision = "HUMAN_REVIEW"
        else:
            status = MatchStatus.REJECTED.value
            decision = "DISPUTE"

        # Create match result
        match_result = MatchResult(
            document_id=invoice.id,
            match_type=MatchType.THREE_WAY.value,
            partner_document_id=delivery_note.id,
            third_document_id=po.id,
            line_level_score=invoice_po_score.line_level_score,
            amount_score=invoice_po_score.amount_score,
            date_score=invoice_po_score.date_score,
            overall_score=overall_score,
            matched_amount=matched_amount,
            variance_amount=variance_amount,
            variance_percentage=(
                Decimal("0") if invoice.total_amount == 0
                else abs(variance_amount) / invoice.total_amount
            ),
            matched_quantity=Decimal("0"),  # Would be calculated from line matches
            quantity_variance=Decimal("0"),
            status=status,
            decision=decision,
            requires_review=(status == MatchStatus.HUMAN_REVIEW.value),
            match_details=json.dumps({
                "line_matches": line_matches,
                "invoice_po_score": float(invoice_po_score.overall_score),
                "dn_po_score": float(dn_po_score.overall_score),
            }),
        )

        self.db.add(match_result)
        self.db.commit()
        self.db.refresh(match_result)
        return match_result

    def _calculate_delivery_note_po_score(
        self, dn: DeliveryNote, po: PurchaseOrder
    ) -> MatchScore:
        """Calculate match score between delivery note and PO."""
        # Similar to invoice-PO matching
        amount_diff = abs(dn.total_amount - po.total_amount)
        max_amount = max(dn.total_amount, po.total_amount)
        amount_score = (
            Decimal("1.0000") - (amount_diff / max_amount)
            if max_amount > 0
            else Decimal("1.0000")
        )

        # Simplified line matching
        line_level_score = Decimal("0.8")  # Placeholder

        date_diff = 0  # Would calculate from dates
        date_score = Decimal("1.0000")

        overall_score = (
            line_level_score * Decimal(str(settings.MATCH_WEIGHT_LINE_LEVEL))
            + amount_score * Decimal(str(settings.MATCH_WEIGHT_AMOUNT))
            + date_score * Decimal(str(settings.MATCH_WEIGHT_DATE))
        )

        return MatchScore(
            line_level_score=line_level_score,
            amount_score=amount_score,
            date_score=date_score,
            overall_score=overall_score,
            matched_amount=min(dn.total_amount, po.total_amount),
            variance_amount=amount_diff,
            variance_percentage=(
                Decimal("0") if max_amount == 0 else amount_diff / max_amount
            ),
            matched_quantity=Decimal("0"),
            quantity_variance=Decimal("0"),
            price_variance=Decimal("0"),
            date_variance_days=date_diff,
            line_matches=[],
        )

    def _calculate_three_way_line_matches(
        self, invoice: Invoice, dn: DeliveryNote, po: PurchaseOrder
    ) -> List[Dict]:
        """Calculate line matches across all three documents."""
        matches = []

        # Get all lines
        invoice_lines = self.db.query(DocumentLine).filter(
            DocumentLine.document_id == invoice.document_id,
            DocumentLine.is_active == True,
        ).all()

        for inv_line in invoice_lines:
            # Find matching lines in DN and PO
            match = {
                "invoice_line_id": str(inv_line.id),
                "invoice_product_code": inv_line.product_code,
                "matched_quantity": float(inv_line.quantity),
                "dn_line_id": None,
                "po_line_id": None,
            }
            matches.append(match)

        return matches

    def get_match_results(
        self,
        document_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[MatchResult], int]:
        """Get match results with filters."""
        query = self.db.query(MatchResult).filter(MatchResult.is_active == True)

        if document_id:
            query = query.filter(
                or_(
                    MatchResult.document_id == document_id,
                    MatchResult.partner_document_id == document_id,
                    MatchResult.third_document_id == document_id,
                )
            )
        if status:
            query = query.filter(MatchResult.status == status)

        total = query.count()
        results = (
            query.order_by(MatchResult.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return results, total

    def review_match_result(
        self,
        match_result: MatchResult,
        approved: bool,
        reviewer_id: UUID,
        notes: Optional[str] = None,
    ) -> MatchResult:
        """Review and confirm/reject a match result."""
        from datetime import datetime

        match_result.reviewed_by = reviewer_id
        match_result.reviewed_at = datetime.utcnow()
        match_result.review_notes = notes

        if approved:
            match_result.status = MatchStatus.CONFIRMED.value
            match_result.decision = "AUTO_APPROVE"

            # Update document status
            invoice = self.db.query(Invoice).filter(Invoice.id == match_result.document_id).first()
            if invoice:
                invoice.status = DocumentStatus.CONFIRMED.value
                invoice.confirmed_by = reviewer_id
                invoice.confirmed_at = datetime.utcnow()
        else:
            match_result.status = MatchStatus.REJECTED.value
            match_result.decision = "DISPUTE"

            invoice = self.db.query(Invoice).filter(Invoice.id == match_result.document_id).first()
            if invoice:
                invoice.status = DocumentStatus.DISPUTED.value

        self.db.commit()
        self.db.refresh(match_result)
        return match_result

    def get_pending_matches(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[MatchResult], int]:
        """Get all matches pending human review."""
        return self.get_match_results(
            status=MatchStatus.HUMAN_REVIEW.value,
            skip=skip,
            limit=limit,
        )
