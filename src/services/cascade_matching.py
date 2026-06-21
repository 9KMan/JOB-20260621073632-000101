// src/services/cascade_matching.py
"""Layer 2: Cascade Matching service for invoice ↔ PO ↔ delivery note matching."""

from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import date
from difflib import SequenceMatcher

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
from app.models.invoice import Invoice, InvoiceLine
from app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from app.models.matching import Match, MatchLine, MatchDecision
from app.services.anchoring import AnchoringService
from app.config import settings


class CascadeMatchingService:
    """
    Layer 2 of the 3-way matching engine.
    
    Performs cascade matching:
    1. Invoice ↔ Purchase Order
    2. Delivery Note ↔ Purchase Order
    3. Invoice ↔ Delivery Note
    
    Each match is scored with weighted criteria:
    - Line-level matching: 70%
    - Amount matching: 20%
    - Date proximity: 10%
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anchoring_service = AnchoringService(db)

    async def match_invoice_to_po(
        self,
        invoice: Invoice,
        po: PurchaseOrder,
    ) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """
        Match invoice lines to PO lines.
        
        Returns tuple of (line_level_score, line_details).
        """
        invoice_lines = invoice.lines
        po_lines = po.lines
        line_scores = []

        # Create item code lookup for PO lines
        po_line_lookup = {line.item_code.lower(): line for line in po_lines}

        for inv_line in invoice_lines:
            line_result = {
                "invoice_line_id": str(inv_line.id),
                "invoice_line_number": inv_line.line_number,
                "item_code": inv_line.item_code,
                "quantity_invoiced": inv_line.quantity_invoiced,
                "unit_price_invoiced": inv_line.unit_price,
                "matched_po_line_id": None,
                "matched": False,
                "score": Decimal("0.0000"),
                "match_type": None,
            }

            # Try exact item code match first
            po_line = po_line_lookup.get(inv_line.item_code.lower())

            if po_line:
                # Calculate line-level match score
                score = self._calculate_line_score(
                    inv_line, po_line, inv_line.quantity_invoiced, po_line.remaining_quantity
                )
                line_result["matched"] = score >= Decimal("0.70")
                line_result["matched_po_line_id"] = str(po_line.id)
                line_result["score"] = score
                line_result["quantity_variance"] = abs(
                    inv_line.quantity_invoiced - po_line.remaining_quantity
                ) / po_line.remaining_quantity if po_line.remaining_quantity > 0 else Decimal("1.00")
                line_result["match_type"] = "exact_code"

            else:
                # Try fuzzy matching for similar item codes
                fuzzy_match = await self._find_fuzzy_match(inv_line, po_lines)
                if fuzzy_match:
                    po_line, similarity = fuzzy_match
                    line_result["matched"] = similarity >= Decimal("0.80")
                    line_result["matched_po_line_id"] = str(po_line.id)
                    line_result["score"] = Decimal(str(similarity)) * Decimal("0.70")
                    line_result["match_type"] = "fuzzy"

            line_scores.append(line_result)

        # Calculate overall line-level score
        if line_scores:
            total_score = sum(ls["score"] for ls in line_scores) / len(line_scores)
        else:
            total_score = Decimal("0.0000")

        return total_score, line_scores

    async def match_delivery_note_to_po(
        self,
        delivery_note: DeliveryNote,
        po: PurchaseOrder,
    ) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """
        Match delivery note lines to PO lines.
        
        Returns tuple of (line_level_score, line_details).
        """
        dn_lines = delivery_note.lines
        po_lines = po.lines
        line_scores = []

        # Create item code lookup for PO lines
        po_line_lookup = {line.item_code.lower(): line for line in po_lines}

        for dn_line in dn_lines:
            line_result = {
                "delivery_note_line_id": str(dn_line.id),
                "delivery_line_number": dn_line.line_number,
                "item_code": dn_line.item_code,
                "quantity_delivered": dn_line.quantity_delivered,
                "matched_po_line_id": None,
                "matched": False,
                "score": Decimal("0.0000"),
                "match_type": None,
            }

            # Try exact item code match first
            po_line = po_line_lookup.get(dn_line.item_code.lower())

            if po_line:
                score = self._calculate_line_score(
                    dn_line, po_line, dn_line.quantity_delivered, po_line.remaining_quantity
                )
                line_result["matched"] = score >= Decimal("0.70")
                line_result["matched_po_line_id"] = str(po_line.id)
                line_result["score"] = score
                line_result["quantity_variance"] = abs(
                    dn_line.quantity_delivered - po_line.remaining_quantity
                ) / po_line.remaining_quantity if po_line.remaining_quantity > 0 else Decimal("1.00")
                line_result["match_type"] = "exact_code"

            else:
                fuzzy_match = await self._find_fuzzy_match(dn_line, po_lines)
                if fuzzy_match:
                    po_line, similarity = fuzzy_match
                    line_result["matched"] = similarity >= Decimal("0.80")
                    line_result["matched_po_line_id"] = str(po_line.id)
                    line_result["score"] = Decimal(str(similarity)) * Decimal("0.70")
                    line_result["match_type"] = "fuzzy"

            line_scores.append(line_result)

        if line_scores:
            total_score = sum(ls["score"] for ls in line_scores) / len(line_scores)
        else:
            total_score = Decimal("0.0000")

        return total_score, line_scores

    async def match_invoice_to_delivery_note(
        self,
        invoice: Invoice,
        delivery_note: DeliveryNote,
    ) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """
        Match invoice lines to delivery note lines.
        
        Returns tuple of (line_level_score, line_details).
        """
        inv_lines = invoice.lines
        dn_lines = delivery_note.lines
        line_scores = []

        # Create item code lookup for DN lines
        dn_line_lookup = {line.item_code.lower(): line for line in dn_lines}

        for inv_line in inv_lines:
            line_result = {
                "invoice_line_id": str(inv_line.id),
                "invoice_line_number": inv_line.line_number,
                "item_code": inv_line.item_code,
                "quantity_invoiced": inv_line.quantity_invoiced,
                "matched_dn_line_id": None,
                "matched": False,
                "score": Decimal("0.0000"),
                "match_type": None,
            }

            # Try exact item code match
            dn_line = dn_line_lookup.get(inv_line.item_code.lower())

            if dn_line:
                # Check if quantities match
                qty_match = abs(inv_line.quantity_invoiced - dn_line.quantity_delivered) <= Decimal("0.01")
                price_match = abs(inv_line.unit_price - dn_line.unit_price) <= Decimal("0.0001")

                score = Decimal("1.0000") if (qty_match and price_match) else Decimal("0.5000")
                line_result["matched"] = qty_match and price_match
                line_result["matched_dn_line_id"] = str(dn_line.id)
                line_result["score"] = score
                line_result["match_type"] = "exact_code"

            line_scores.append(line_result)

        if line_scores:
            total_score = sum(ls["score"] for ls in line_scores) / len(line_scores)
        else:
            total_score = Decimal("0.0000")

        return total_score, line_scores

    def calculate_amount_score(
        self,
        invoice_amount: Decimal,
        po_amount: Decimal,
        tolerance_percentage: Decimal = Decimal("0.05"),
    ) -> Decimal:
        """
        Calculate amount matching score.
        
        Score is 1.0 if amounts are within tolerance, decreasing linearly outside.
        """
        if po_amount == 0:
            return Decimal("0.0000") if invoice_amount > 0 else Decimal("1.0000")

        variance = abs(invoice_amount - po_amount) / po_amount

        if variance <= tolerance_percentage:
            return Decimal("1.0000")
        elif variance <= Decimal("0.10"):  # 10% variance
            return Decimal("0.8000")
        elif variance <= Decimal("0.20"):  # 20% variance
            return Decimal("0.5000")
        else:
            return Decimal("0.1000")

    def calculate_date_score(
        self,
        invoice_date: date,
        po_date: date,
        delivery_date: Optional[date] = None,
    ) -> Decimal:
        """
        Calculate date proximity score.
        
        Base score on days between invoice date and PO date,
        with bonus if delivery note date is provided and aligns.
        """
        days_diff = abs((invoice_date - po_date).days)

        if days_diff <= 7:
            base_score = Decimal("1.0000")
        elif days_diff <= 14:
            base_score = Decimal("0.9000")
        elif days_diff <= 30:
            base_score = Decimal("0.7000")
        elif days_diff <= 60:
            base_score = Decimal("0.5000")
        else:
            base_score = Decimal("0.3000")

        # Bonus if delivery date aligns
        if delivery_date:
            delivery_days_diff = abs((delivery_date - po_date).days)
            if delivery_days_diff <= 7:
                base_score = min(Decimal("1.0000"), base_score + Decimal("0.1000"))

        return base_score

    def calculate_total_score(
        self,
        line_level_score: Decimal,
        amount_score: Decimal,
        date_score: Decimal,
    ) -> Decimal:
        """
        Calculate weighted total match score.
        
        Weights:
        - Line-level: 70%
        - Amount: 20%
        - Date: 10%
        """
        total = (
            line_level_score * Decimal(str(settings.MATCH_WEIGHT_LINE_LEVEL)) +
            amount_score * Decimal(str(settings.MATCH_WEIGHT_AMOUNT)) +
            date_score * Decimal(str(settings.MATCH_WEIGHT_DATE))
        )
        return round(total, 4)

    async def _find_fuzzy_match(
        self,
        document_line: Any,
        po_lines: List[PurchaseOrderLine],
    ) -> Optional[Tuple[PurchaseOrderLine, Decimal]]:
        """Find best fuzzy match for item code."""
        best_match = None
        best_similarity = Decimal("0.00")

        for po_line in po_lines:
            similarity = self._string_similarity(
                document_line.item_code.lower(),
                po_line.item_code.lower(),
            )

            # Also check description similarity
            desc_similarity = self._string_similarity(
                document_line.item_description.lower(),
                po_line.item_description.lower(),
            )

            combined_similarity = (similarity * 0.7) + (desc_similarity * 0.3)

            if combined_similarity > best_similarity:
                best_similarity = Decimal(str(combined_similarity))
                best_match = po_line

        if best_similarity >= Decimal("0.60"):
            return best_match, best_similarity

        return None

    @staticmethod
    def _string_similarity(s1: str, s2: str) -> Decimal:
        """Calculate string similarity using SequenceMatcher."""
        return Decimal(str(SequenceMatcher(None, s1, s2).ratio()))

    @staticmethod
    def _calculate_line_score(
        document_line: Any,
        po_line: PurchaseOrderLine,
        doc_quantity: Decimal,
        po_remaining_quantity: Decimal,
    ) -> Decimal:
        """Calculate line-level match score."""
        score = Decimal("1.0000")

        # Quantity variance penalty
        if po_remaining_quantity > 0:
            qty_variance = abs(doc_quantity - po_remaining_quantity) / po_remaining_quantity
            if qty_variance > Decimal("0.10"):  # > 10% variance
                score -= Decimal("0.2000")

        # Price variance penalty
        price_variance = abs(document_line.unit_price - po_line.unit_price) / po_line.unit_price \
            if po_line.unit_price > 0 else Decimal("0.00")
        if price_variance > Decimal("0.01"):  # > 1% price variance
            score -= Decimal("0.1000")

        return max(score, Decimal("0.0000"))

    async def perform_full_cascade_match(
        self,
        invoice: Invoice,
        delivery_note: Optional[DeliveryNote],
        po: PurchaseOrder,
    ) -> Dict[str, Any]:
        """
        Perform full cascade matching for 3-way match.
        
        Returns comprehensive match results with all scores.
        """
        results = {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "purchase_order_id": str(po.id),
            "purchase_order_number": po.po_number,
            "delivery_note_id": str(delivery_note.id) if delivery_note else None,
            "delivery_note_number": delivery_note.dn_number if delivery_note else None,
            "line_level_score": Decimal("0.0000"),
            "amount_score": Decimal("0.0000"),
            "date_score": Decimal("0.0000"),
            "total_score": Decimal("0.0000"),
            "line_details": [],
        }

        # Step 1: Invoice ↔ PO matching
        inv_po_score, inv_po_lines = await self.match_invoice_to_po(invoice, po)
        results["line_level_score"] = inv_po_score

        # Step 2: Delivery Note ↔ PO matching (if provided)
        if delivery_note:
            dn_po_score, dn_po_lines = await self.match_delivery_note_to_po(delivery_note, po)
            # Average with invoice score for line-level
            results["line_level_score"] = (inv_po_score + dn_po_score) / 2

            # Step 3: Invoice ↔ Delivery Note matching
            inv_dn_score, inv_dn_lines = await self.match_invoice_to_delivery_note(invoice, delivery_note)
            # Adjust line-level score based on 3-way consistency
            results["line_level_score"] = results["line_level_score"] * Decimal("0.8") + inv_dn_score * Decimal("0.2")

        # Step 3: Calculate amount score
        results["amount_score"] = self.calculate_amount_score(invoice.total_amount, po.total_amount)

        # Step 4: Calculate date score
        results["date_score"] = self.calculate_date_score(
            invoice.invoice_date,
            po.po_date,
            delivery_note.dn_date if delivery_note else None,
        )

        # Step 5: Calculate total score
        results["total_score"] = self.calculate_total_score(
            results["line_level_score"],
            results["amount_score"],
            results["date_score"],
        )

        # Combine all line details
        results["line_details"] = {
            "invoice_to_po": inv_po_lines,
            "delivery_note_to_po": dn_po_lines if delivery_note else [],
            "invoice_to_delivery_note": inv_dn_lines if delivery_note else [],
        }

        return results
