// src/services/matching_service.py
"""3-way matching service implementing Layer 1, 2, and 3 logic."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.config import get_settings
from src.api.schemas.matching import (
    LineMatchDetail,
    MatchResults,
    MatchDecision,
)
from src.models.document import Document, DocumentLine, DocumentType
from src.models.matching import MatchResult, MatchResultLineMatch, MatchStatus, MatchType


class MatchingService:
    """Service for performing 3-way matching operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.weights = self.settings.MATCHING_WEIGHTS

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Fetch a document by ID with its lines."""
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.lines))
            .where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def perform_3way_match(
        self,
        invoice: Optional[Document],
        delivery_note: Optional[Document],
        purchase_order: Document
    ) -> MatchResults:
        """
        Perform 3-way matching across Invoice, Delivery Note, and Purchase Order.
        
        Layer 1: Anchoring - Use PO as single source of truth
        Layer 2: Cascade Matching - Match invoice↔PO, DN↔PO, invoice↔DN
        Layer 3: Balance Resolution - Track partial matches and balances
        """
        warnings = []
        
        # Layer 1: Anchoring - Ensure we have a PO to anchor to
        if not purchase_order:
            raise ValueError("Purchase Order is required for 3-way matching")

        # Layer 2: Cascade Matching
        invoice_po_score = Decimal("0")
        dn_po_score = Decimal("0")
        invoice_dn_score = Decimal("0")
        line_matches = []

        # Match Invoice to PO
        if invoice:
            invoice_po_score, invoice_po_matches = self._match_documents(
                source=invoice,
                target=purchase_order
            )
            line_matches.extend(invoice_po_matches)

        # Match Delivery Note to PO
        if delivery_note:
            dn_po_score, dn_po_matches = self._match_documents(
                source=delivery_note,
                target=purchase_order
            )
            line_matches.extend(dn_po_matches)

        # Match Invoice to Delivery Note (if both exist)
        if invoice and delivery_note:
            invoice_dn_score, invoice_dn_matches = self._match_documents(
                source=invoice,
                target=delivery_note
            )
            line_matches.extend(invoice_dn_matches)

        # Calculate overall score with weights
        overall_score = self._calculate_overall_score(
            invoice_po_score=invoice_po_score,
            dn_po_score=dn_po_score,
            invoice_dn_score=invoice_dn_score,
            has_invoice=invoice is not None,
            has_delivery_note=delivery_note is not None
        )

        # Layer 3: Balance Resolution
        amount_variance = Decimal("0")
        quantity_variance = Decimal("0")
        date_variance_days = 0

        if invoice:
            amount_variance = abs(invoice.total_amount - purchase_order.total_amount)
            date_variance_days = abs((invoice.document_date - purchase_order.document_date).days)

        if invoice and delivery_note:
            quantity_variance = self._calculate_quantity_variance(invoice, delivery_note)

        balance_status = self._determine_balance_status(
            amount_variance=amount_variance,
            quantity_variance=quantity_variance
        )

        # Generate warnings
        if amount_variance > Decimal("0"):
            tolerance = purchase_order.total_amount * Decimal(str(self.settings.BALANCE_TOLERANCE_PERCENT / 100))
            if amount_variance > tolerance:
                warnings.append(f"Amount variance ${amount_variance} exceeds tolerance")

        if date_variance_days > 30:
            warnings.append(f"Date variance of {date_variance_days} days is significant")

        if overall_score < Decimal(str(self.settings.MATCHING_THRESHOLD_PENDING)):
            warnings.append("Match score below threshold - manual review required")

        return MatchResults(
            overall_score=float(overall_score),
            line_matches=line_matches,
            amount_variance=amount_variance,
            quantity_variance=quantity_variance,
            date_variance_days=date_variance_days,
            balance_status=balance_status,
            has_warnings=len(warnings) > 0,
            warnings=warnings,
            invoice_po_match=float(invoice_po_score),
            dn_po_match=float(dn_po_score),
            invoice_dn_match=float(invoice_dn_score)
        )

    def _match_documents(
        self,
        source: Document,
        target: Document
    ) -> tuple[Decimal, list[LineMatchDetail]]:
        """
        Match two documents at the line level.
        
        Returns a match score and list of line-level match details.
        """
        match_score = Decimal("0")
        matches: list[LineMatchDetail] = []

        source_lines = {line.line_number: line for line in source.lines}
        target_lines = {line.line_number: line for line in target.lines}

        matched_source_lines = set()
        matched_target_lines = set()

        # Exact line number matching
        for line_num in source_lines:
            if line_num in target_lines:
                source_line = source_lines[line_num]
                target_line = target_lines[line_num]

                score, detail = self._calculate_line_match(
                    source_line=source_line,
                    target_line=target_line,
                    source_type=source.document_type.value,
                    target_type=target.document_type.value
                )

                match_score += score
                matches.append(detail)
                matched_source_lines.add(line_num)
                matched_target_lines.add(line_num)

        # Fuzzy matching for unmatched lines
        for line_num in source_lines:
            if line_num not in matched_source_lines:
                source_line = source_lines[line_num]
                best_match = None
                best_score = Decimal("0")

                for t_line_num in target_lines:
                    if t_line_num not in matched_target_lines:
                        target_line = target_lines[t_line_num]
                        score = self._fuzzy_line_match(source_line, target_line)
                        if score > best_score:
                            best_score = score
                            best_match = t_line_num

                if best_match and best_score > Decimal("0.5"):
                    target_line = target_lines[best_match]
                    score, detail = self._calculate_line_match(
                        source_line=source_line,
                        target_line=target_line,
                        source_type=source.document_type.value,
                        target_type=target.document_type.value
                    )
                    match_score += score * Decimal("0.8")  # Penalty for fuzzy match
                    matches.append(detail)
                    matched_source_lines.add(line_num)
                    matched_target_lines.add(best_match)

        # Calculate normalized score
        max_possible = max(len(source.lines), len(target.lines), 1)
        normalized_score = match_score / Decimal(max_possible)
        normalized_score = min(normalized_score, Decimal("1.0"))

        return normalized_score, matches

    def _calculate_line_match(
        self,
        source_line: DocumentLine,
        target_line: DocumentLine,
        source_type: str,
        target_type: str
    ) -> tuple[Decimal, LineMatchDetail]:
        """Calculate match score for a single line pair."""
        scores = []

        # Item code match (if available)
        if source_line.item_code and target_line.item_code:
            if source_line.item_code == target_line.item_code:
                scores.append(Decimal("1.0"))
            else:
                scores.append(Decimal("0.0"))
        else:
            scores.append(Decimal("0.5"))  # Neutral if no item codes

        # Quantity match
        quantity_diff = abs(source_line.quantity - target_line.quantity)
        quantity_match = quantity_diff == Decimal("0")
        scores.append(Decimal("1.0") if quantity_match else Decimal("0.0"))

        # Amount match
        amount_diff = abs(source_line.total_amount - target_line.total_amount)
        amount_match = amount_diff == Decimal("0")
        scores.append(Decimal("1.0") if amount_match else Decimal("0.0"))

        # Line score
        line_score = sum(scores) / Decimal(len(scores)) if scores else Decimal("0")

        detail = LineMatchDetail(
            source_line_id=source_line.id,
            target_line_id=target_line.id,
            match_score=float(line_score),
            quantity_match=quantity_match,
            amount_match=amount_match,
            item_code_match=source_line.item_code == target_line.item_code if source_line.item_code and target_line.item_code else False
        )

        return line_score, detail

    def _fuzzy_line_match(
        self,
        source_line: DocumentLine,
        target_line: DocumentLine
    ) -> Decimal:
        """Calculate fuzzy match score based on description similarity."""
        score = Decimal("0")
        count = Decimal("0")

        # Item code similarity
        if source_line.item_code and target_line.item_code:
            if source_line.item_code.lower() == target_line.item_code.lower():
                score += Decimal("1.0")
            count += Decimal("1.0")

        # Description similarity (simple check)
        if source_line.description and target_line.description:
            source_words = set(source_line.description.lower().split())
            target_words = set(target_line.description.lower().split())
            if source_words and target_words:
                overlap = len(source_words & target_words)
                total = len(source_words | target_words)
                if total > 0:
                    score += Decimal(str(overlap / total))
                count += Decimal("1.0")

        return score / count if count > 0 else Decimal("0")

    def _calculate_overall_score(
        self,
        invoice_po_score: Decimal,
        dn_po_score: Decimal,
        invoice_dn_score: Decimal,
        has_invoice: bool,
        has_delivery_note: bool
    ) -> Decimal:
        """Calculate overall weighted match score."""
        total_weight = Decimal("0")
        weighted_sum = Decimal("0")

        if has_invoice:
            weighted_sum += invoice_po_score * Decimal(str(self.weights["line_level"]))
            total_weight += Decimal(str(self.weights["line_level"]))

        if has_delivery_note:
            weighted_sum += dn_po_score * Decimal(str(self.weights["line_level"]))
            total_weight += Decimal(str(self.weights["line_level"]))

        # Amount weight
        weighted_sum += Decimal("0.2") * (invoice_po_score if has_invoice else Decimal("0"))
        total_weight += Decimal("0.2")

        # Date weight
        weighted_sum += Decimal("0.1") * (invoice_po_score if has_invoice else Decimal("0"))
        total_weight += Decimal("0.1")

        return weighted_sum / total_weight if total_weight > 0 else Decimal("0")

    def _calculate_quantity_variance(
        self,
        invoice: Document,
        delivery_note: Document
    ) -> Decimal:
        """Calculate quantity variance between invoice and delivery note."""
        invoice_qty = sum(line.quantity for line in invoice.lines)
        dn_qty = sum(line.quantity for line in delivery_note.lines)
        return abs(invoice_qty - dn_qty)

    def _determine_balance_status(
        self,
        amount_variance: Decimal,
        quantity_variance: Decimal
    ) -> str:
        """Determine balance status based on variances."""
        if amount_variance == Decimal("0") and quantity_variance == Decimal("0"):
            return "BALANCED"
        elif amount_variance < Decimal("100") and quantity_variance < Decimal("1"):
            return "PARTIAL_BALANCE"
        else:
            return "UNBALANCED"

    async def save_match_result(
        self,
        invoice_id: UUID,
        delivery_note_id: Optional[UUID],
        purchase_order_id: UUID,
        match_results: MatchResults,
        decision: MatchDecision
    ) -> MatchResult:
        """Save match result and related data to database."""
        # Create main match result
        match_result = MatchResult(
            invoice_id=str(invoice_id),
            delivery_note_id=str(delivery_note_id) if delivery_note_id else None,
            purchase_order_id=str(purchase_order_id),
            status=MatchStatus(decision.status),
            overall_score=Decimal(str(match_results.overall_score)),
            invoice_po_match_score=Decimal(str(match_results.invoice_po_match)),
            dn_po_match_score=Decimal(str(match_results.dn_po_match)),
            invoice_dn_match_score=Decimal(str(match_results.invoice_dn_match)),
            amount_variance=match_results.amount_variance,
            quantity_variance=match_results.quantity_variance,
            date_variance_days=match_results.date_variance_days,
            balance_status=match_results.balance_status,
            warnings=match_results.warnings,
            match_details={
                "has_warnings": match_results.has_warnings,
                "warnings": match_results.warnings
            }
        )

        self.db.add(match_result)
        await self.db.flush()

        # Save line matches
        for line_match in match_results.line_matches:
            line_match_record = MatchResultLineMatch(
                match_result_id=match_result.id,
                source_document_type="INVOICE",  # Simplified - would need actual tracking
                source_line_id=str(line_match.source_line_id),
                source_line_number=0,  # Would need to track this
                target_document_type="PO",
                target_line_id=str(line_match.target_line_id),
                target_line_number=0,
                match_type=MatchType.PARTIAL if line_match.match_score < 1.0 else MatchType.EXACT,
                match_score=Decimal(str(line_match.match_score)),
                quantity_variance=Decimal("0"),  # Would calculate from actual values
                amount_variance=Decimal("0")
            )
            self.db.add(line_match_record)

        await self.db.commit()
        await self.db.refresh(match_result)

        return match_result
