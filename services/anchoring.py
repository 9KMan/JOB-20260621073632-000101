python
// services/anchoring.py
"""Layer 1 of the matching cascade: PO anchoring.

Given an invoice, anchoring identifies which purchase order the invoice belongs
to. Strategies, in priority order:

1. Explicit PO number on the invoice header (not modelled here; reserved for a
   later phase). When present, anchoring is trivially ``score=100``.
2. Vendor + total-amount match within tolerance against any open PO.
3. Vendor + first-line SKU + first-line unit-price within tolerance.

The returned :class:`AnchorResult` is consumed by :mod:`services.cascade`,
which performs line-level matching.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.enums import DocumentStatus
from models.invoice import Invoice, InvoiceLine
from models.purchase_order import PurchaseOrder

# Tolerance constants are surfaced on the result so downstream layers can
# explain why a candidate was rejected.
PRICE_EPSILON = Decimal("0.0001")
QTY_EPSILON = Decimal("0.0001")


@dataclass
class AnchorCandidate:
    purchase_order_id: uuid.UUID
    po_number: str
    score: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class AnchorResult:
    invoice_id: uuid.UUID
    candidates: List[AnchorCandidate] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def best(self) -> Optional[AnchorCandidate]:
        return self.candidates[0] if self.candidates else None


async def anchor_invoice(session: AsyncSession, invoice: Invoice) -> AnchorResult:
    """Run the anchoring strategies for one invoice.

    The session is used read-only; no writes happen during anchoring.
    """
    settings = get_settings()
    result = AnchorResult(invoice_id=invoice.id)

    if not invoice.lines:
        result.notes.append("invoice has no lines; cannot anchor")
        return result

    open_pos = await _fetch_open_pos_for_vendor(session, invoice.vendor_id)
    if not open_pos:
        result.notes.append(f"no open purchase orders for vendor {invoice.vendor_id}")
        return result

    invoice_total = invoice.total_amount
    first_line: InvoiceLine = invoice.lines[0]
    tolerance = Decimal(str(settings.tolerance_price))

    for po in open_pos:
        candidate = AnchorCandidate(
            purchase_order_id=po.id,
            po_number=po.po_number,
            score=0.0,
        )

        # Strategy 2: total amount within tolerance.
        if invoice_total > 0 and po.total_amount > 0:
            delta = abs(invoice_total - po.total_amount) / po.total_amount
            if delta <= tolerance:
                candidate.score += 50.0
                candidate.reasons.append(
                    f"total-amount match within {tolerance:.2%} tolerance"
                )
            else:
                candidate.reasons.append(
                    f"total-amount delta {delta:.2%} exceeds tolerance"
                )

        # Strategy 3: first-line SKU + unit price (if invoice line has a SKU).
        if first_line.sku:
            line_match = _first_line_match(first_line, po.lines, tolerance)
            if line_match is not None:
                candidate.score += 50.0
                candidate.reasons.append(
                    f"first-line SKU+price match on PO line {line_match.line_number}"
                )

        # Require the PO to be in INGESTED status (not already closed).
        if po.status not in {DocumentStatus.INGESTED, DocumentStatus.MATCHED}:
            candidate.reasons.append(f"PO status {po.status.value} not eligible")

        result.candidates.append(candidate)

    # Best candidate first; ties broken by PO id for determinism.
    result.candidates.sort(
        key=lambda c: (-c.score, str(c.purchase_order_id))
    )
    return result


def _first_line_match(invoice_line: InvoiceLine, po_lines: Iterable, tolerance: Decimal):
    """Return the best matching PO line by SKU+price, or None.

    Kept synchronous so anchoring remains easy to unit-test without a session.
    """
    best = None
    best_delta = Decimal("Infinity")
    for pol in po_lines:
        if not invoice_line.sku or pol.sku != invoice_line.sku:
            continue
        if pol.unit_price <= 0:
            continue
        delta = abs(invoice_line.unit_price - pol.unit_price) / pol.unit_price
        if delta <= tolerance and delta < best_delta:
            best = pol
            best_delta = delta
    return best


async def _fetch_open_pos_for_vendor(
    session: AsyncSession, vendor_id: uuid.UUID
) -> List[PurchaseOrder]:
    stmt = (
        select(PurchaseOrder)
        .where(PurchaseOrder.vendor_id == vendor_id)
        .where(PurchaseOrder.status.in_([DocumentStatus.INGESTED, DocumentStatus.MATCHED]))
        .order_by(PurchaseOrder.order_date.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

