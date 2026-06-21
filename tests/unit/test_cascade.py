python
// tests/unit/test_cascade.py
"""Unit tests for the cascade line-matching service."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from models.enums import MatchLayer
from services.cascade import _jaccard, _match_one_line, _tokens, cascade_match


def _po_line(*, line_number: int = 1, sku: str = "SKU-1", description: str = "Widget",
             ordered_qty: Decimal = Decimal("10"), unit_price: Decimal = Decimal("9.99")):
    from models.purchase_order import PurchaseOrderLine

    return PurchaseOrderLine(
        purchase_order_id=uuid.uuid4(),
        line_number=line_number,
        sku=sku,
        description=description,
        ordered_qty=ordered_qty,
        unit_price=unit_price,
        line_total=ordered_qty * unit_price,
        uom="EA",
    )


def _invoice_line(*, line_number: int = 1, sku: str | None = "SKU-1",
                  description: str = "Widget",
                  quantity: Decimal = Decimal("10"),
                  unit_price: Decimal = Decimal("9.99")):
    from models.invoice import InvoiceLine

    return InvoiceLine(
        id=uuid.uuid4(),
        line_number=line_number,
        sku=sku,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        line_total=quantity * unit_price,
        uom="EA",
        tax_amount=Decimal("0"),
    )


def test_match_one_line_sku_qty_price_match_scores_95():
    pol = _po_line()
    inv = _invoice_line()
    decision = _match_one_line(inv, [pol], [], Decimal("0.02"), Decimal("0.01"))
    assert decision.score == 95.0
    assert decision.decision_layer == MatchLayer.CASCADE
    assert decision.purchase_order_line_id == pol.id


def test_match_one_line_description_similarity_above_floor():
    pol = _po_line(sku=None, description="Premium Carbon Steel Widget 12mm")
    inv = _invoice_line(sku=None, description="Premium Carbon Steel Widget 12mm")
    decision = _match_one_line(inv, [pol], [], Decimal("0.02"), Decimal("0.01"))
    assert decision.purchase_order_line_id == pol.id
    assert decision.decision_layer == MatchLayer.CASCADE
    assert decision.score >= 70.0


def test_match_one_line_returns_no_candidate_when_below_floor():
    pol = _po_line(sku=None, description="Hammer drill 18V")
    inv = _invoice_line(sku=None, description="Inkjet cartridge cyan")
    decision = _match_one_line(inv, [pol], [], Decimal("0.02"), Decimal("0.01"))
    assert decision.purchase_order_line_id is None
    assert decision.score == 0.0


def test_match_one_line_uses_promoted_alias_when_available():
    from models.cross_ref import CrossRef

    alias = CrossRef(
        vendor_id=uuid.uuid4(),
        sku="SKU-1",
        canonical_description="Widget",
        alias_description="Widget Pro",
        confirmation_count=5,
        avg_confidence=Decimal("0.95"),
        is_promoted=True,
        last_seen_at=Decimal("0"),
    )
    pol = _po_line(sku="SKU-1")
    inv = _invoice_line(description="Widget Pro")
    decision = _match_one_line(inv, [pol], [alias], Decimal("0.02"), Decimal("0.01"))
    assert decision.decision_layer == MatchLayer.LEARNING
    assert decision.score == 98.0


def test_tokens_and_jaccard_helpers():
    a = _tokens("Premium Carbon Steel Widget")
    b = _tokens("Premium Steel Widget")
    j = _jaccard(a, b)
    assert 0.0 < j < 1.0


@pytest.mark.asyncio
async def test_cascade_match_returns_empty_when_no_anchor(vendor_id):
    from models.enums import DocumentStatus
    from models.invoice import Invoice
    from services.anchoring import AnchorResult
    from datetime import datetime, timezone

    inv = Invoice(
        id=uuid.uuid4(),
        invoice_number="INV-1",
        vendor_id=vendor_id,
        vendor_name="Acme",
        currency="USD",
        invoice_date=datetime.now(timezone.utc).date(),
        received_at=datetime.now(timezone.utc),
        subtotal=Decimal("0"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("0"),
        status=DocumentStatus.INGESTED,
        source="manual",
    )
    result = await cascade_match(object(), inv, AnchorResult(invoice_id=inv.id))  # type: ignore[arg-type]
    assert result.line_decisions == []

