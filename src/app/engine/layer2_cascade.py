// src/app/engine/layer2_cascade.py
"""Layer 2: Cascade Matching - Performs weighted scoring across documents."""

from typing import Tuple, Dict, List
from decimal import Decimal
from datetime import date, timedelta

from src.app.config import get_settings
from src.app.models import Invoice, InvoiceLine, DeliveryNote, DeliveryNoteLine, PurchaseOrder, PurchaseOrderLine

settings = get_settings()


class Layer2Cascade:
    """
    Layer 2 - Cascade Matching Engine
    
    Performs cascade matching in order:
    1. Invoice ↔ Purchase Order
    2. Delivery Note ↔ Purchase Order
    3. Invoice ↔ Delivery Note
    
    Each match is scored with weighted criteria:
    - Line Level: 70%
    - Amount: 20%
    - Date: 10%
    """

    def __init__(self):
        """Initialize Layer 2 cascade matching engine."""
        self.weights = {
            "line_level": settings.match_weight_line_level,
            "amount": settings.match_weight_amount,
            "date": settings.match_weight_date
        }

    def match_invoice_po(
        self,
        invoice: Invoice,
        po: PurchaseOrder
    ) -> Tuple[float, Dict[str, float], Dict[str, Decimal]]:
        """
        Match invoice against purchase order.
        
        Args:
            invoice: Invoice object with lines
            po: Purchase order object with lines
            
        Returns:
            Tuple of (overall_score, score_breakdown, variance_data)
        """
        # Calculate individual scores
        line_score = self._calculate_line_level_score(
            invoice.lines, po.lines
        )
        amount_score = self._calculate_amount_score(
            invoice.total_amount, po.total_amount
        )
        date_score = self._calculate_date_score(
            invoice.invoice_date, po.order_date
        )

        # Calculate weighted overall score
        overall_score = (
            line_score * self.weights["line_level"] +
            amount_score * self.weights["amount"] +
            date_score * self.weights["date"]
        )

        # Calculate variance
        variance = {
            "amount": invoice.total_amount - po.total_amount,
            "quantity": self._calculate_quantity_variance(invoice.lines, po.lines),
            "date_days": abs((invoice.invoice_date - po.order_date).days)
        }

        return overall_score, {
            "line_level": line_score,
            "amount": amount_score,
            "date": date_score
        }, variance

    def match_dn_po(
        self,
        dn: DeliveryNote,
        po: PurchaseOrder
    ) -> Tuple[float, Dict[str, float], Dict[str, Decimal]]:
        """
        Match delivery note against purchase order.
        
        Args:
            dn: Delivery note object with lines
            po: Purchase order object with lines
            
        Returns:
            Tuple of (overall_score, score_breakdown, variance_data)
        """
        # Calculate individual scores
        line_score = self._calculate_line_level_score(
            dn.lines, po.lines
        )
        amount_score = self._calculate_amount_score(
            dn.total_amount, po.total_amount
        )
        date_score = self._calculate_date_score(
            dn.delivery_date, po.order_date, tolerance_days=7
        )

        # Calculate weighted overall score
        overall_score = (
            line_score * self.weights["line_level"] +
            amount_score * self.weights["amount"] +
            date_score * self.weights["date"]
        )

        # Calculate variance
        variance = {
            "amount": dn.total_amount - po.total_amount,
            "quantity": self._calculate_quantity_variance(dn.lines, po.lines),
            "date_days": abs((dn.delivery_date - po.order_date).days)
        }

        return overall_score, {
            "line_level": line_score,
            "amount": amount_score,
            "date": date_score
        }, variance

    def match_invoice_dn(
        self,
        invoice: Invoice,
        dn: DeliveryNote
    ) -> Tuple[float, Dict[str, float], Dict[str, Decimal]]:
        """
        Match invoice against delivery note.
        
        Args:
            invoice: Invoice object with lines
            dn: Delivery note object with lines
            
        Returns:
            Tuple of (overall_score, score_breakdown, variance_data)
        """
        # Calculate individual scores
        line_score = self._calculate_line_level_score(
            invoice.lines, dn.lines
        )
        amount_score = self._calculate_amount_score(
            invoice.total_amount, dn.total_amount
        )
        date_score = self._calculate_date_score(
            invoice.invoice_date, dn.delivery_date, tolerance_days=30
        )

        # Calculate weighted overall score
        overall_score = (
            line_score * self.weights["line_level"] +
            amount_score * self.weights["amount"] +
            date_score * self.weights["date"]
        )

        # Calculate variance
        variance = {
            "amount": invoice.total_amount - dn.total_amount,
            "quantity": self._calculate_quantity_variance(invoice.lines, dn.lines),
            "date_days": abs((invoice.invoice_date - dn.delivery_date).days)
        }

        return overall_score, {
            "line_level": line_score,
            "amount": amount_score,
            "date": date_score
        }, variance

    def match_three_way(
        self,
        invoice: Invoice,
        dn: DeliveryNote,
        po: PurchaseOrder
    ) -> Tuple[float, Dict[str, float], Dict[str, Decimal]]:
        """
        Perform full 3-way matching.
        
        Matches invoice, delivery note, and purchase order together.
        Score is the minimum of pairwise scores (all must match well).
        
        Args:
            invoice: Invoice object with lines
            dn: Delivery note object (can be None)
            po: Purchase order object with lines
            
        Returns:
            Tuple of (overall_score, score_breakdown, variance_data)
        """
        # Calculate pairwise scores
        inv_po_score, inv_po_scores, inv_po_var = self.match_invoice_po(invoice, po)
        
        if dn:
            dn_po_score, dn_po_scores, dn_po_var = self.match_dn_po(dn, po)
            inv_dn_score, inv_dn_scores, inv_dn_var = self.match_invoice_dn(invoice, dn)
            
            # Use minimum score (all three must agree)
            overall_score = min(inv_po_score, dn_po_score, inv_dn_score)
            
            # Average the score components
            scores = {
                "line_level": (inv_po_scores["line_level"] + 
                             dn_po_scores["line_level"] + 
                             inv_dn_scores["line_level"]) / 3,
                "amount": (inv_po_scores["amount"] + 
                          dn_po_scores["amount"] + 
                          inv_dn_scores["amount"]) / 3,
                "date": (inv_po_scores["date"] + 
                        dn_po_scores["date"] + 
                        inv_dn_scores["date"]) / 3
            }
            
            # Sum variances
            variance = {
                "amount": inv_po_var["amount"] + dn_po_var["amount"],
                "quantity": inv_po_var["quantity"] + dn_po_var["quantity"],
                "date_days": max(inv_po_var["date_days"], dn_po_var["date_days"], inv_dn_var["date_days"])
            }
        else:
            # No delivery note, use invoice-PO matching only
            overall_score = inv_po_score
            scores = inv_po_scores
            variance = inv_po_var

        return overall_score, scores, variance

    def _calculate_line_level_score(
        self,
        lines1: List,
        lines2: List
    ) -> float:
        """
        Calculate line-level matching score.
        
        Compares item codes and quantities across all lines.
        Score is based on:
        - Matched line count / total unique lines
        - Quantity variance on matched lines
        """
        if not lines1 or not lines2:
            return 0.0

        # Build item code lookup for both
        items1 = {line.item_code: line for line in lines1}
        items2 = {line.item_code: line for line in lines2}

        # Find matching items
        matched_items = set(items1.keys()) & set(items2.keys())
        total_unique_items = set(items1.keys()) | set(items2.keys())

        if not total_unique_items:
            return 0.0

        # Line match ratio
        match_ratio = len(matched_items) / len(total_unique_items)

        # Calculate quantity accuracy for matched items
        quantity_scores = []
        for item_code in matched_items:
            line1 = items1[item_code]
            line2 = items2[item_code]
            qty_accuracy = self._quantity_accuracy(
                float(line1.quantity), float(line2.quantity)
            )
            quantity_scores.append(qty_accuracy)

        avg_quantity_score = sum(quantity_scores) / len(quantity_scores) if quantity_scores else 0

        # Combined score: 60% match ratio, 40% quantity accuracy
        return (match_ratio * 0.6) + (avg_quantity_score * 0.4)

    def _calculate_amount_score(
        self,
        amount1: Decimal,
        amount2: Decimal
    ) -> float:
        """
        Calculate amount matching score.
        
        Uses percentage-based scoring:
        - 100% if amounts match exactly
        - Decreases proportionally with variance
        - Zero if variance exceeds 50%
        """
        if amount2 == 0:
            return 0.0 if amount1 != 0 else 1.0

        variance_pct = abs(float(amount1 - amount2)) / float(amount2)
        
        if variance_pct == 0:
            return 1.0
        elif variance_pct >= 0.5:
            return 0.0
        else:
            return 1.0 - (variance_pct * 2)

    def _calculate_date_score(
        self,
        date1: date,
        date2: date,
        tolerance_days: int = 14
    ) -> float:
        """
        Calculate date matching score.
        
        Score decreases linearly from 100% at exact match
        to 0% when difference exceeds tolerance.
        """
        days_diff = abs((date1 - date2).days)

        if days_diff == 0:
            return 1.0
        elif days_diff >= tolerance_days:
            return 0.0
        else:
            return 1.0 - (days_diff / tolerance_days)

    def _calculate_quantity_variance(
        self,
        lines1: List,
        lines2: List
    ) -> Decimal:
        """Calculate total quantity variance between line sets."""
        total1 = sum(line.quantity for line in lines1)
        total2 = sum(line.quantity for line in lines2)
        return total1 - total2

    def _quantity_accuracy(self, qty1: float, qty2: float) -> float:
        """Calculate quantity accuracy as a ratio."""
        if qty2 == 0:
            return 0.0 if qty1 != 0 else 1.0
        
        diff = abs(qty1 - qty2)
        ratio = diff / qty2
        
        if ratio == 0:
            return 1.0
        elif ratio >= 1.0:
            return 0.0
        else:
            return 1.0 - ratio
