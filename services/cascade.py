python
// services/cascade.py
"""Layer 2 of the matching cascade: per-line matching.

Given an :class:`AnchorResult` from Layer 1, this module matches each invoice
line to the best candidate PO line. Strategies, in order:

1. SKU + exact quantity within tolerance and price within tolerance.
2. Description similarity (token-set Jaccard) above a configurable floor.
3. Promoted cross_ref lookup as a fast path before falling back to (1)/(2).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.cross_ref import CrossRef
from models.enums import MatchLayer
from models.invoice import Invoice, InvoiceLine
from models.purchase_order import PurchaseOrderLine
from services.anchoring import AnchorCandidate, AnchorResult

DESCRIPTION_JACCARD_FLOOR = 0.55


@dataclass
class LineDecision:
    invoice_line_id: uuid.UUID
    purchase_order_line_id: Optional[uuid.UUID]
    score: float
    decision_layer: MatchLayer
    reasons: List[str] = field(default_factory=list)

    @property
    def layer(self) -> MatchLayer:
        return self.decision_layer

    @property
    def decision(self):  # forward reference; populated by scoring layer
        return None  # type: ignore[return-value]


@dataclass
class CascadeResult:
    invoice_id: uuid.UUID
    anchor: AnchorCandidate
    line_decisions: List[LineDecision] = field(default_factory=list)


async def cascade_match(
    session: AsyncSession,
    invoice: Invoice,
    anchor_result: AnchorResult,
) -> CascadeResult:
    """Run line-level matching for each invoice line.

    If anchoring produced no candidate, we return an empty result; the API
    layer is responsible for marking the invoice as ``needs_review``.
    """
    best = anchor_result.best
    if best is None:
        return CascadeResult(invoice_id=invoice.id, anchor=None)  # type: ignore[arg-type]

    settings = get_settings()
    price_tol = Decimal(str(settings.tolerance_price))
    qty_tol = Decimal(str(settings.tolerance_qty))

    po_lines = await _fetch_po_lines(session, best.purchase_order_id)
    promoted = await _fetch_promoted_aliases(session, invoice.vendor_id)

    decisions: List[LineDecision] = []
    for inv_line in invoice.lines:
        decision = _match_one_line(inv_line, po_lines, promoted, price_tol, qty_tol)
        decisions.append(decision)

    return CascadeResult(
        invoice_id=invoice.id,
        anchor=best,
        line_decisions=decisions,
    )


def _match_one_line(
    inv_line: InvoiceLine,
    po_lines: List[PurchaseOrderLine],
    promoted: List[CrossRef],
    price_tol: Decimal,
    qty_tol: Decimal,
) -> LineDecision:
    base_reasons: List[str] = []

    # Strategy 0: promoted alias fast-path (description-only matches).
    if inv_line.sku:
        alias_hit = next(
            (
                cr
                for cr in promoted
                if cr.sku == inv_line.sku
                and _normalized(cr.alias_description) == _normalized(inv_line.description)
            ),
            None,
        )
        if alias_hit is not None:
            target = next((p for p in po_lines if p.sku == inv_line.sku), None)
            if target is not None:
                return LineDecision(
                    invoice_line_id=inv_line.id,
                    purchase_order_line_id=target.id,
                    score=98.0,
                    decision_layer=MatchLayer.LEARNING,
                    reasons=["promoted cross_ref alias matched description exactly"],
                )

    # Strategy 1: SKU + qty + price match.
    if inv_line.sku:
        sku_candidates = [p for p in po_lines if p.sku == inv_line.sku]
        if sku_candidates:
            best = _best_sku_match(inv_line, sku_candidates, price_tol, qty_tol)
            if best is not None:
                return LineDecision(
                    invoice_line_id=inv_line.id,
                    purchase_order_line_id=best.line.id,
                    score=95.0,
                    decision_layer=MatchLayer.CASCADE,
                    reasons=[
                        f"SKU match with qty delta {best.qty_delta:.2%} and price delta {best.price_delta:.2%}"
                    ],
                )
            base_reasons.append("SKU found but qty/price outside tolerance")

    # Strategy 2: description similarity across all PO lines.
    best_desc: Optional[LineDecision] = None
    best_jaccard = 0.0
    inv_tokens = _tokens(inv_line.description)
    for pol in po_lines:
        jaccard = _jaccard(inv_tokens, _tokens(pol.description))
        if jaccard < DESCRIPTION_JACCARD_FLOOR:
            continue
        score = 70.0 + (jaccard - DESCRIPTION_JACCARD_FLOOR) * 100.0
        cand = LineDecision(
            invoice_line_id=inv_line.id,
            purchase_order_line_id=pol.id,
            score=round(score, 2),
            decision_layer=MatchLayer.CASCADE,
            reasons=[f"description Jaccard={jaccard:.2f}"],
        )
        if cand.score > (best_desc.score if best_desc else 0.0):
            best_desc = cand
            best_jaccard = jaccard

    if best_desc is not None:
        return best_desc

    return LineDecision(
        invoice_line_id=inv_line.id,
        purchase_order_line_id=None,
        score=0.0,
        decision_layer=MatchLayer.NONE,
        reasons=base_reasons + ["no candidate line matched"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _SkuMatch:
    line: PurchaseOrderLine
    qty_delta: float
    price_delta: float


def _best_sku_match(
    inv_line: InvoiceLine,
    candidates: List[PurchaseOrderLine],
    price_tol: Decimal,
    qty_tol: Decimal,
) -> Optional[_SkuMatch]:
    best: Optional[_SkuMatch] = None
    for pol in candidates:
        if pol.unit_price <= 0 or pol.ordered_qty <= 0:
            continue
        qty_delta = abs(inv_line.quantity - pol.ordered_qty) / pol.ordered_qty
        if qty_delta > qty_tol:
            continue
        price_delta = abs(inv_line.unit_price - pol.unit_price) / pol.unit_price
        if price_delta > price_tol:
            continue
        cand = _SkuMatch(line=pol, qty_delta=float(qty_delta), price_delta=float(price_delta))
        if best is None or (qty_delta + price_delta) < (best.qty_delta + best.price_delta):
            best = cand
    return best


def _normalized(s: str) -> str:
    return " ".join(s.lower().split())


def _tokens(s: str) -> set[str]:
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s.lower())
    return {tok for tok in cleaned.split() if len(tok) > 1}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


async def _fetch_po_lines(
    session: AsyncSession, purchase_order_id: uuid.UUID
) -> List[PurchaseOrderLine]:
    stmt = (
        select(PurchaseOrderLine)
        .where(PurchaseOrderLine.purchase_order_id == purchase_order_id)
        .order_by(PurchaseOrderLine.line_number)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _fetch_promoted_aliases(
    session: AsyncSession, vendor_id: uuid.UUID
) -> List[CrossRef]:
    stmt = (
        select(CrossRef)
        .where(CrossRef.vendor_id == vendor_id)
        .where(CrossRef.is_promoted.is_(True))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

