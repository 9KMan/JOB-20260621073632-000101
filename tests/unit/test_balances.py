python
// tests/unit/test_balances.py
"""Unit tests for the balances service."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from models.balance_ledger import BalanceLedger, LedgerEventType
from services.balances import can_post_invoice


def _ledger(*, ordered_qty: Decimal = Decimal("100"),
            received_qty: Decimal = Decimal("0"),
            invoiced_qty: Decimal = Decimal("0"),
            ordered_value: Decimal = Decimal("1000"),
            invoiced_value: Decimal = Decimal("0")) -> BalanceLedger:
    open_qty = ordered_qty - received_qty
    open_value = ordered_value - invoiced_value
    return BalanceLedger(
        id=uuid.uuid4(),
        purchase_order_line_id=uuid.uuid4(),
        ordered_qty=ordered_qty,
        received_qty=received_qty,
        invoiced_qty=invoiced_qty,
        ordered_value=ordered_value,
        invoiced_value=invoiced_value,
        open_qty=open_qty,
        open_value=open_value,
        last_event_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        currency="USD",
    )


def test_can_post_invoice_allows_full_match():
    ledger = _ledger()
    assert can_post_invoice(
        ledger, qty=Decimal("100"), value=Decimal("1000"),
        qty_tolerance=Decimal("0.01"), value_tolerance=Decimal("0.02"),
    )


def test_can_post_invoice_allows_within_tolerance_overrun():
    ledger = _ledger()
    # Over by 0.5% on qty (within 1% tolerance) and 1.5% on value (within 2%).
    assert can_post_invoice(
        ledger, qty=Decimal("100.5"), value=Decimal("1015"),
        qty_tolerance=Decimal("0.01"), value_tolerance=Decimal("0.02"),
    )


def test_can_post_invoice_blocks_outside_tolerance():
    ledger = _ledger()
    assert not can_post_invoice(
        ledger, qty=Decimal("110"), value=Decimal("1000"),
        qty_tolerance=Decimal("0.01"), value_tolerance=Decimal("0.02"),
    )


def test_can_post_invoice_blocks_double_invoicing():
    ledger = _ledger(invoiced_qty=Decimal("100"), invoiced_value=Decimal("1000"))
    assert not can_post_invoice(
        ledger, qty=Decimal("10"), value=Decimal("100"),
        qty_tolerance=Decimal("0.01"), value_tolerance=Decimal("0.02"),
    )


@pytest.mark.asyncio
async def test_post_event_updates_snapshot_for_goods_received():
    from datetime import datetime, timezone
    from services.balances import post_event

    ledger = _ledger()
    entry = await post_event(
        object(),  # type: ignore[arg-type]
        ledger,
        event_type=LedgerEventType.GOODS_RECEIVED,
        delta_qty=Decimal("50"),
        delta_value=Decimal("500"),
        reference_type="delivery_note",
        reference_id=uuid.uuid4(),
    )
    assert ledger.received_qty == Decimal("50")
    assert ledger.open_qty == Decimal("50")
    assert entry.event_type == LedgerEventType.GOODS_RECEIVED


@pytest.mark.asyncio
async def test_post_event_invoice_posted_updates_value():
    from services.balances import post_event

    ledger = _ledger()
    await post_event(
        object(),  # type: ignore[arg-type]
        ledger,
        event_type=LedgerEventType.INVOICE_POSTED,
        delta_qty=Decimal("30"),
        delta_value=Decimal("300"),
        reference_type="invoice",
        reference_id=uuid.uuid4(),
    )
    assert ledger.invoiced_qty == Decimal("30")
    assert ledger.invoiced_value == Decimal("300")
    assert ledger.open_value == Decimal("700")

