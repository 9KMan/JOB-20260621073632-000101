// src/services/matching_service.py
"""Matching service for 3-way matching engine."""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_cached_settings
from models.document import Document, DocumentLineItem, DocumentType, DocumentStatus
from models.matching import (
    MatchResult,
    MatchLineItem,
    MatchStatus,
    MatchType,
)
from services.document_service import DocumentService

settings = get_cached_settings()


class MatchingService:
    """Service for 3-way matching operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.document_service = DocumentService(session)

    async def perform_full_match(
        self, invoice_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> MatchResult:
        """
        Perform complete 3-way match for an invoice.
        
        This implements the full matching cascade:
        1. Layer 1 - Anchor to PO
        2. Layer 2 - Cascade matching
        3. Layer 3 - Balance resolution
        """
        # Get invoice
        invoice = await self.document_service.get_document_by_id(
            invoice_id, include_line_items=True
        )
        
        if not invoice or invoice.document_type != DocumentType.INVOICE:
            raise ValueError("Invalid invoice")
        
        # Layer 1: Find anchor PO
        anchor_po = await self._find_anchor_po(invoice)
        
        if not anchor_po:
            # No PO found, create result with PO_INVOICE status
            return await self._create_match_result(
                invoice_id=invoice_id,
                match_type=MatchType.PO_INVOICE,
                status=MatchStatus.PENDING,
                reason="No matching Purchase Order found",
            )
        
        # Layer 2: Cascade matching
        # Match PO ↔ Invoice
        po_invoice_match = await self._match_two_documents(anchor_po, invoice)
        
        # Find and match delivery note
        delivery_note = await self._find_anchor_delivery(invoice, anchor_po)
        
        if delivery_note:
            # Match PO ↔ Delivery
            po_delivery_match = await self._match_two_documents(
                anchor_po, delivery_note
            )
            
            # Match Invoice ↔ Delivery
            invoice_delivery_match = await self._match_two_documents(
                invoice, delivery_note
            )
            
            # Create 3-way match result
            match_result = await self._create_three_way_match(
                anchor_po,
                invoice,
                delivery_note,
                user_id,
            )
        else:
            # 2-way match (PO + Invoice)
            match_result = await self._create_two_way_match(
                anchor_po,
                invoice,
                MatchType.PO_INVOICE,
                user_id,
            )
        
        return match_result

    async def _find_anchor_po(self, invoice: Document) -> Optional[Document]:
        """Layer 1: Find PO anchor for invoice."""
        # Get open POs by supplier
        open_pos = await self.document_service.get_open_pos_by_supplier(
            invoice.supplier_id
        )
        
        # Try to match by PO number in supplier reference
        for po in open_pos:
            if invoice.supplier_reference and invoice.supplier_reference == po.document_number:
                return po
        
        # Try to match by document number
        for po in open_pos:
            if invoice.supplier_reference and invoice.supplier_reference in po.document_number:
                return po
        
        # Return most recent open PO if no exact match
        return open_pos[0] if open_pos else None

    async def _find_anchor_delivery(
        self, invoice: Document, po: Document
    ) -> Optional[Document]:
        """Find delivery note anchor for invoice and PO."""
        # Get pending delivery notes by supplier
        deliveries = await self.document_service.get_pending_delivery_notes_by_supplier(
            invoice.supplier_id
        )
        
        # Try to match by supplier reference
        for delivery in deliveries:
            if invoice.supplier_reference and invoice.supplier_reference == delivery.document_number:
                return delivery
        
        # Try to match by date proximity (within 7 days of invoice)
        invoice_date = invoice.document_date
        for delivery in deliveries:
            if delivery.document_date:
                date_diff = abs((invoice_date - delivery.document_date).days)
                if date_diff <= 7:
                    return delivery
        
        return None

    async def _match_two_documents(
        self, doc1: Document, doc2: Document
    ) -> Dict:
        """Match two documents and return match scores."""
        scores = self._calculate_match_scores(doc1, doc2)
        
        # Match line items
        line_matches = await self._match_line_items(doc1, doc2)
        
        return {
            "scores": scores,
            "line_matches": line_matches,
        }

    def _calculate_match_scores(
        self, doc1: Document, doc2: Document
    ) -> Dict[str, float]:
        """Calculate weighted match scores between two documents."""
        # Amount score (20% weight)
        amount_score = self._calculate_amount_score(doc1, doc2)
        
        # Date score (10% weight)
        date_score = self._calculate_date_score(doc1, doc2)
        
        # Line level score (70% weight)
        line_score = self._calculate_line_level_score(doc1, doc2)
        
        # Total weighted score
        total_score = (
            line_score * (settings.MATCH_WEIGHT_LINE_LEVEL / 100)
            + amount_score * (settings.MATCH_WEIGHT_AMOUNT / 100)
            + date_score * (settings.MATCH_WEIGHT_DATE / 100)
        )
        
        return {
            "total_score": total_score,
            "line_level_score": line_score,
            "amount_score": amount_score,
            "date_score": date_score,
        }

    def _calculate_amount_score(
        self, doc1: Document, doc2: Document
    ) -> float:
        """Calculate amount match score (0-100)."""
        if doc1.total_amount == 0:
            return 0.0
        
        variance = abs(doc1.total_amount - doc2.total_amount)
        max_amount = max(doc1.total_amount, doc2.total_amount)
        
        score = max(0, 100 - (variance / max_amount * 100))
        return float(score)

    def _calculate_date_score(
        self, doc1: Document, doc2: Document
    ) -> float:
        """Calculate date match score (0-100)."""
        if not doc1.document_date or not doc2.document_date:
            return 50.0  # Neutral score if dates missing
        
        days_diff = abs((doc1.document_date - doc2.document_date).days)
        
        # Perfect match = 100, within 7 days = 80, within 30 days = 50
        if days_diff == 0:
            return 100.0
        elif days_diff <= 7:
            return 90.0
        elif days_diff <= 30:
            return 70.0
        else:
            return max(0, 50 - (days_diff - 30) * 2)

    def _calculate_line_level_score(
        self, doc1: Document, doc2: Document
    ) -> float:
        """Calculate line item match score (0-100)."""
        items1 = doc1.line_items or []
        items2 = doc2.line_items or []
        
        if not items1 or not items2:
            return 50.0  # Neutral if no line items
        
        matched_count = 0
        partial_count = 0
        
        for item1 in items1:
            best_match = None
            best_score = 0
            
            for item2 in items2:
                score = self._compare_line_items(item1, item2)
                if score > best_score:
                    best_score = score
                    best_match = item2
            
            if best_score >= 90:
                matched_count += 1
            elif best_score >= 60:
                partial_count += 1
        
        total_items = max(len(items1), len(items2))
        
        return ((matched_count * 100) + (partial_count * 50)) / total_items

    def _compare_line_items(
        self, item1: DocumentLineItem, item2: DocumentLineItem
    ) -> float:
        """Compare two line items and return similarity score (0-100)."""
        score = 0.0
        weights = {"product_code": 40, "quantity": 30, "amount": 30}
        
        # Product code match
        if item1.product_code and item2.product_code:
            if item1.product_code.lower() == item2.product_code.lower():
                score += weights["product_code"]
            elif item1.product_code.lower() in item2.product_code.lower():
                score += weights["product_code"] * 0.7
            elif item2.product_code.lower() in item1.product_code.lower():
                score += weights["product_code"] * 0.7
        
        # Quantity match
        if item1.quantity and item2.quantity:
            variance = abs(item1.quantity - item2.quantity)
            max_qty = max(item1.quantity, item2.quantity)
            
            if variance == 0:
                score += weights["quantity"]
            else:
                qty_score = max(0, 100 - (variance / max_qty * 100))
                score += weights["quantity"] * (qty_score / 100)
        
        # Amount match
        if item1.line_total and item2.line_total:
            variance = abs(item1.line_total - item2.line_total)
            max_amt = max(item1.line_total, item2.line_total)
            
            if variance == 0:
                score += weights["amount"]
            else:
                amt_score = max(0, 100 - (variance / max_amt * 100))
                score += weights["amount"] * (amt_score / 100)
        
        return score

    async def _match_line_items(
        self, doc1: Document, doc2: Document
    ) -> List[Dict]:
        """Match line items between two documents."""
        items1 = doc1.line_items or []
        items2 = doc2.line_items or []
        
        matches = []
        
        for item1 in items1:
            best_match = None
            best_score = 0
            
            for item2 in items2:
                score = self._compare_line_items(item1, item2)
                if score > best_score:
                    best_score = score
                    best_match = item2
            
            if best_match:
                matches.append({
                    "line1": item1,
                    "line2": best_match,
                    "score": best_score,
                    "is_matched": best_score >= 90,
                    "match_percentage": best_score,
                })
        
        return matches

    async def _create_three_way_match(
        self,
        po: Document,
        invoice: Document,
        delivery: Document,
        user_id: Optional[uuid.UUID],
    ) -> MatchResult:
        """Create a 3-way match result."""
        # Calculate overall scores
        scores = self._calculate_3way_scores(po, invoice, delivery)
        
        # Match line items across all three
        line_matches = await self._match_three_way_line_items(po, invoice, delivery)
        
        # Create match result
        match_result = MatchResult(
            match_type=MatchType.THREE_WAY,
            status=MatchStatus.PENDING,
            purchase_order_id=po.id,
            invoice_id=invoice.id,
            delivery_note_id=delivery.id,
            total_score=scores["total_score"],
            line_level_score=scores["line_level_score"],
            amount_score=scores["amount_score"],
            date_score=scores["date_score"],
            po_amount=po.total_amount,
            invoice_amount=invoice.total_amount,
            delivery_amount=delivery.total_amount,
            variance_amount=abs(po.total_amount - invoice.total_amount),
            total_line_items=len(line_matches),
            matched_line_items=sum(1 for m in line_matches if m["is_matched"]),
            partial_line_items=sum(1 for m in line_matches if m["is_partial"]),
            unmatched_line_items=sum(1 for m in line_matches if not m["is_matched"] and not m["is_partial"]),
            created_by=user_id,
        )
        
        self.session.add(match_result)
        await self.session.flush()
        
        # Create line item matches
        for lm in line_matches:
            match_line = MatchLineItem(
                match_result_id=match_result.id,
                po_line_item_id=lm["po_line"].id if lm["po_line"] else None,
                invoice_line_item_id=lm["invoice_line"].id if lm["invoice_line"] else None,
                delivery_line_item_id=lm["delivery_line"].id if lm["delivery_line"] else None,
                is_matched=lm["is_matched"],
                match_percentage=lm["score"],
                po_quantity=lm["po_line"].quantity if lm["po_line"] else None,
                invoice_quantity=lm["invoice_line"].quantity if lm["invoice_line"] else None,
                delivery_quantity=lm["delivery_line"].quantity if lm["delivery_line"] else None,
                quantity_variance=lm.get("quantity_variance", Decimal("0")),
                po_amount=lm["po_line"].line_total if lm["po_line"] else None,
                invoice_amount=lm["invoice_line"].line_total if lm["invoice_line"] else None,
                delivery_amount=lm["delivery_line"].line_total if lm["delivery_line"] else None,
                amount_variance=lm.get("amount_variance", Decimal("0")),
            )
            self.session.add(match_line)
        
        await self.session.flush()
        
        return match_result

    async def _create_two_way_match(
        self,
        doc1: Document,
        doc2: Document,
        match_type: MatchType,
        user_id: Optional[uuid.UUID],
    ) -> MatchResult:
        """Create a 2-way match result."""
        scores = self._calculate_match_scores(doc1, doc2)
        line_matches = await self._match_line_items(doc1, doc2)
        
        if match_type == MatchType.PO_INVOICE:
            po_id = doc1.id if doc1.document_type == DocumentType.PURCHASE_ORDER else doc2.id
            invoice_id = doc1.id if doc1.document_type == DocumentType.INVOICE else doc2.id
        else:
            po_id = None
            invoice_id = doc2.id
        
        match_result = MatchResult(
            match_type=match_type,
            status=MatchStatus.PENDING,
            purchase_order_id=po_id,
            invoice_id=invoice_id,
            total_score=scores["total_score"],
            line_level_score=scores["line_level_score"],
            amount_score=scores["amount_score"],
            date_score=scores["date_score"],
            po_amount=doc1.total_amount if doc1.document_type == DocumentType.PURCHASE_ORDER else doc2.total_amount,
            invoice_amount=doc1.total_amount if doc1.document_type == DocumentType.INVOICE else doc2.total_amount,
            variance_amount=abs(doc1.total_amount - doc2.total_amount),
            total_line_items=len(line_matches),
            matched_line_items=sum(1 for m in line_matches if m["is_matched"]),
            partial_line_items=0,
            unmatched_line_items=sum(1 for m in line_matches if not m["is_matched"]),
            created_by=user_id,
        )
        
        self.session.add(match_result)
        await self.session.flush()
        
        return match_result

    def _calculate_3way_scores(
        self, po: Document, invoice: Document, delivery: Document
    ) -> Dict[str, float]:
        """Calculate scores for 3-way matching."""
        # Average scores from all pairs
        po_invoice_scores = self._calculate_match_scores(po, invoice)
        po_delivery_scores = self._calculate_match_scores(po, delivery)
        invoice_delivery_scores = self._calculate_match_scores(invoice, delivery)
        
        return {
            "total_score": (
                po_invoice_scores["total_score"]
                + po_delivery_scores["total_score"]
                + invoice_delivery_scores["total_score"]
            ) / 3,
            "line_level_score": (
                po_invoice_scores["line_level_score"]
                + po_delivery_scores["line_level_score"]
                + invoice_delivery_scores["line_level_score"]
            ) / 3,
            "amount_score": (
                po_invoice_scores["amount_score"]
                + po_delivery_scores["amount_score"]
                + invoice_delivery_scores["amount_score"]
            ) / 3,
            "date_score": (
                po_invoice_scores["date_score"]
                + po_delivery_scores["date_score"]
                + invoice_delivery_scores["date_score"]
            ) / 3,
        }

    async def _match_three_way_line_items(
        self, po: Document, invoice: Document, delivery: Document
    ) -> List[Dict]:
        """Match line items across three documents."""
        po_items = {i.product_code: i for i in (po.line_items or [])}
        invoice_items = {i.product_code: i for i in (invoice.line_items or [])}
        delivery_items = {i.product_code: i for i in (delivery.line_items or [])}
        
        all_codes = set(po_items.keys()) | set(invoice_items.keys()) | set(delivery_items.keys())
        
        matches = []
        
        for code in all_codes:
            po_item = po_items.get(code)
            invoice_item = invoice_items.get(code)
            delivery_item = delivery_items.get(code)
            
            # Calculate match score
            score = 0
            count = 0
            
            if po_item and invoice_item:
                score += self._compare_line_items(po_item, invoice_item)
                count += 1
            
            if po_item and delivery_item:
                score += self._compare_line_items(po_item, delivery_item)
                count += 1
            
            if invoice_item and delivery_item:
                score += self._compare_line_items(invoice_item, delivery_item)
                count += 1
            
            avg_score = score / count if count > 0 else 0
            
            matches.append({
                "po_line": po_item,
                "invoice_line": invoice_item,
                "delivery_line": delivery_item,
                "score": avg_score,
                "is_matched": avg_score >= 90,
                "is_partial": 60 <= avg_score < 90,
                "quantity_variance": self._calc_quantity_variance(po_item, invoice_item, delivery_item),
                "amount_variance": self._calc_amount_variance(po_item, invoice_item, delivery_item),
            })
        
        return matches

    def _calc_quantity_variance(
        self, po_item, invoice_item, delivery_item
    ) -> Decimal:
        """Calculate quantity variance across documents."""
        quantities = []
        
        if po_item and po_item.quantity:
            quantities.append(po_item.quantity)
        if invoice_item and invoice_item.quantity:
            quantities.append(invoice_item.quantity)
        if delivery_item and delivery_item.quantity:
            quantities.append(delivery_item.quantity)
        
        if len(quantities) < 2:
            return Decimal("0")
        
        return max(quantities) - min(quantities)

    def _calc_amount_variance(
        self, po_item, invoice_item, delivery_item
    ) -> Decimal:
        """Calculate amount variance across documents."""
        amounts = []
        
        if po_item and po_item.line_total:
            amounts.append(po_item.line_total)
        if invoice_item and invoice_item.line_total:
            amounts.append(invoice_item.line_total)
        if delivery_item and delivery_item.line_total:
            amounts.append(delivery_item.line_total)
        
        if len(amounts) < 2:
            return Decimal("0")
        
        return max(amounts) - min(amounts)

    async def _create_match_result(
        self,
        invoice_id: uuid.UUID,
        match_type: MatchType,
        status: MatchStatus,
        reason: str,
    ) -> MatchResult:
        """Create a match result for failed matches."""
        match_result = MatchResult(
            match_type=match_type,
            status=status,
            invoice_id=invoice_id,
            total_score=0.0,
            line_level_score=0.0,
            amount_score=0.0,
            date_score=0.0,
            decision_reason=reason,
        )
        
        self.session.add(match_result)
        await self.session.flush()
        
        return match_result

    async def get_match_result_by_id(
        self, match_id: uuid.UUID
    ) -> Optional[MatchResult]:
        """Get match result by ID."""
        query = select(MatchResult).where(MatchResult.id == match_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_match_results(
        self,
        status: Optional[MatchStatus] = None,
        match_type: Optional[MatchType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MatchResult], int]:
        """Get paginated match results."""
        conditions = []
        
        if status:
            conditions.append(MatchResult.status == status)
        
        if match_type:
            conditions.append(MatchResult.match_type == match_type)
        
        # Count
        count_query = select(func.count(MatchResult.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Data
        offset = (page - 1) * page_size
        data_query = select(MatchResult)
        if conditions:
            data_query = data_query.where(and_(*conditions))
        
        data_query = (
            data_query.order_by(MatchResult.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.session.execute(data_query)
        matches = list(result.scalars().all())
        
        return matches, total

    async def update_match_status(
        self,
        match_id: uuid.UUID,
        status: MatchStatus,
        confirmed_by: Optional[uuid.UUID] = None,
    ) -> Optional[MatchResult]:
        """Update match status."""
        match = await self.get_match_result_by_id(match_id)
        
        if not match:
            return None
        
        match.status = status
        
        if confirmed_by:
            match.confirmed_by = confirmed_by
            match.confirmed_at = datetime.utcnow()
        
        await self.session.flush()
        
        return match
