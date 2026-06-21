python
// services/balances.py
"""Balance ledger service.

Maintains the running ``BalanceLedger`` snapshot and the immutable
``BalanceLedgerEntry`` event log. Callers post events; the snapshot is
recomputed transactionally.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.balance_ledger import BalanceLedger, BalanceLedgerEntry, LedgerEventType
from models.purchase_order import PurchaseOrderLine


@dataclass
class BalanceSnapshot:
    purchase_order_line_id: uuid.UUID
    ordered_qty: Decimal
    received_qty: Decimal
    invoiced_qty: Decimal
    open_qty: Decimal
    ordered_value: Decimal
    invoiced_value: Decimal
    open_value: Decimal

    @classmethod
    def from_orm(cls, ledger: BalanceLedger) -> "BalanceSnapshot":
        return cls(
            purchase_order_line_id=ledger.purchase_order_line_id,
            ordered_qty=ledger.ordered_qty,
            received_qty=ledger.received_qty,
            invoiced_qty=ledger.invoiced_qty,
            open_qty=ledger.open_qty,
            ordered_value=ledger.ordered_value,
            invoiced_value=ledger.invoiced_value,
            open_value=ledger.open_value,
        )


async def get_or_create_ledger(
    session: AsyncSession,
    po_line: PurchaseOrderLine,
) -> BalanceLedger:
    """Return the current ledger, opening a new snapshot if none exists."""
    ledger = await session.get(BalanceLedger, po_line.id)
    if ledger is None:
        ledger = BalanceLedger(
            id=po_line.id,
            purchase_order_line_id=po_line.id,
            ordered_qty=po_line.ordered_qty,
            received_qty=po_line.received_qty,
            invoiced_qty=po_line.invoiced_qty,
            ordered_value=po_line.line_total,
            invoiced_value=Decimal("0"),
            open_qty=po_line.ordered_qty - po_line.received_qty,
            open_value=po_line.line_total,
            last_event_at=datetime.now(timezone.utc),
            currency="USD",
        )
        session.add(ledger)
        await session.flush()
    return ledger


async def post_event(
    session: AsyncSession,
    ledger: BalanceLedger,
    *,
    event_type: LedgerEventType,
    delta_qty: Decimal,
    delta_value: Decimal,
    reference_type: str,
    reference_id: uuid.UUID,
    note: Optional[str] = None,
) -> BalanceLedgerEntry:
    """Append a ledger event and update the snapshot in the same transaction."""
    entry = BalanceLedgerEntry(
        balance_ledger_id=ledger.id,
        purchase_order_line_id=ledger.purchase_order_line_id,
        event_type=event_type,
        delta_qty=delta_qty,
        delta_value=delta_value,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
    )
    session.add(entry)

    if event_type == LedgerEventType.GOODS_RECEIVED:
        ledger.received_qty += delta_qty
    elif event_type == LedgerEventType.INVOICE_POSTED:
        ledger.invoiced_qty += delta_qty
        ledger.invoiced_value += delta_value
    elif event_type == LedgerEventType.REVERSAL:
        ledger.invoiced_qty -= delta_qty
        ledger.invoiced_value -= delta_value
        ledger.received_qty -= delta_qty
    # ADJUSTMENT and OPENING_BALANCE leave the event for audit only.

    ledger.open_qty = ledger.ordered_qty - ledger.received_qty
    ledger.open_value = ledger.ordered_value - ledger.invoiced_value
    ledger.last_event_at = datetime.now(timezone.utc)

    await session.flush()
    return entry


async def get_ledger(
    session: AsyncSession, purchase_order_line_id: uuid.UUID
) -> Optional[BalanceLedger]:
    return await session.get(BalanceLedger, purchase_order_line_id)


async def list_entries(
    session: AsyncSession,
    purchase_order_line_id: uuid.UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> List[BalanceLedgerEntry]:
    stmt = (
        select(BalanceLedgerEntry)
        .where(BalanceLedgerEntry.purchase_order_line_id == purchase_order_line_id)
        .order_by(BalanceLedgerEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def can_post_invoice(
    ledger: BalanceLedger,
    *,
    qty: Decimal,
    value: Decimal,
    qty_tolerance: Decimal,
    value_tolerance: Decimal,
) -> bool:
    """Return True if posting ``qty``/``value`` keeps balances within tolerance.

    Tolerance is applied independently to quantity and value so that a small
    price variance does not block matching.
    """
    new_open_qty = ledger.open_qty - qty
    new_open_value = ledger.open_value - value
    qty_within = new_open_qty >= -qty_tolerance * ledger.ordered_qty
    value_within = new_open_value >= -value_tolerance * ledger.ordered_value
    return qty_within and value_within

