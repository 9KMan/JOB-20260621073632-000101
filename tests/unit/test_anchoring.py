python
// tests/unit/test_anchoring.py
"""Unit tests for the anchoring service."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from services.anchoring import _first_line_match, anchor_invoice  # noqa: F401


def _po_line(*, line_number: int = 1, sku: str = "SKU-1", unit_price: Decimal = Decimal("9.99")):
    from models.purchase_order import PurchaseOrderLine

    return PurchaseOrderLine(
        purchase_order_id=uuid.uuid4(),
        line_number=line_number,
        sku=sku,
        description="Widget",
        ordered_qty=Decimal("10"),
        unit_price=unit_price,
        line_total=Decimal("99.90"),
        uom="EA",
    )


def _invoice_line(*, sku: str | None = "SKU-1", unit_price: Decimal = Decimal("9.99")):
    from models.invoice import InvoiceLine

    return InvoiceLine(
        line_number=1,
        sku=sku,
        description="Widget",
        quantity=Decimal("10"),
        unit_price=unit_price,
        line_total=Decimal("99.90"),
        uom="EA",
        tax_amount=Decimal("0"),
    )


def test_first_line_match_within_tolerance_returns_line():
    pol = _po_line(unit_price=Decimal("9.99"))
    inv_line = _invoice_line(unit_price=Decimal("10.00"))  # ~0.1% above
    result = _first_line_match(inv_line, [pol], Decimal("0.02"))
    assert result is pol


def test_first_line_match_outside_tolerance_returns_none():
    pol = _po_line(unit_price=Decimal("9.99"))
    inv_line = _invoice_line(unit_price=Decimal("15.00"))  # 50% above
    assert _first_line_match(inv_line, [pol], Decimal("0.02")) is None


def test_first_line_match_skips_when_no_sku():
    pol = _po_line(sku=None)
    inv_line = _invoice_line(sku=None)
    assert _first_line_match(inv_line, [pol], Decimal("0.02")) is None


def test_first_line_match_picks_smallest_delta():
    pol_far = _po_line(line_number=1, unit_price=Decimal("12.00"))
    pol_near = _po_line(line_number=2, unit_price=Decimal("10.00"))
    inv_line = _invoice_line(unit_price=Decimal("10.05"))
    result = _first_line_match(inv_line, [pol_far, pol_near], Decimal("0.02"))
    assert result is pol_near


@pytest.mark.asyncio
async def test_anchor_returns_empty_when_invoice_has_no_lines(vendor_id):
    from models.enums import DocumentStatus
    from models.invoice import Invoice
    from datetime import datetime, timezone

    inv = Invoice(
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
    # Empty line list.
    result = await anchor_invoice(object(), inv)  # type: ignore[arg-type]
    assert result.candidates == []
    assert "no lines" in result.notes[0]

