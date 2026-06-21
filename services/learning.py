python
// services/learning.py
"""Learning loop: cross-reference promotion and confirmation updates.

The :class:`CrossRef` table captures (vendor_id, sku, alias_description)
triples. Each successful cascade match may call :func:`record_confirmation`
to bump the count. When a triple crosses both the minimum-confirmation count
and the average-confidence threshold, :func:`maybe_promote` flips its
``is_promoted`` flag so it becomes a fast-path rule in the cascade.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.cross_ref import CrossRef


@dataclass
class ConfirmationUpdate:
    cross_ref_id: uuid.UUID
    new_count: int
    new_avg_confidence: Decimal
    promoted: bool


async def record_confirmation(
    session: AsyncSession,
    *,
    vendor_id: uuid.UUID,
    sku: str,
    canonical_description: str,
    alias_description: str,
    confidence: float,
) -> ConfirmationUpdate:
    """Record one confirmation and return the updated state.

    The row is keyed by ``(vendor_id, sku, alias_description)``; canonical
    description may evolve over time, but the alias is what the invoice line
    actually said, so we keep it as part of the key.
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be in [0, 1]")
    if not sku:
        raise ValueError("sku is required")

    stmt = select(CrossRef).where(
        CrossRef.vendor_id == vendor_id,
        CrossRef.sku == sku,
        CrossRef.alias_description == alias_description,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()

    now_epoch = Decimal(str(datetime.now(timezone.utc).timestamp()))
    if row is None:
        row = CrossRef(
            vendor_id=vendor_id,
            sku=sku,
            canonical_description=canonical_description,
            alias_description=alias_description,
            confirmation_count=1,
            avg_confidence=Decimal(str(confidence)),
            is_promoted=False,
            last_seen_at=now_epoch,
        )
        session.add(row)
        await session.flush()
    else:
        # Running average update: new_avg = (old_avg * n + x) / (n + 1)
        n = row.confirmation_count
        old_avg = row.avg_confidence
        new_avg = (old_avg * Decimal(n) + Decimal(str(confidence))) / Decimal(n + 1)
        row.confirmation_count = n + 1
        row.avg_confidence = new_avg
        row.canonical_description = canonical_description
        row.last_seen_at = now_epoch
        await session.flush()

    promoted = await maybe_promote(session, row)
    return ConfirmationUpdate(
        cross_ref_id=row.id,
        new_count=row.confirmation_count,
        new_avg_confidence=row.avg_confidence,
        promoted=promoted,
    )


async def maybe_promote(session: AsyncSession, row: CrossRef) -> bool:
    """Promote ``row`` if it meets the configured thresholds.

    Returns True when this call performed the promotion (idempotent).
    """
    settings = get_settings()
    if row.is_promoted:
        return False
    qualifies = (
        row.confirmation_count >= settings.cross_ref_min_confirmations
        and row.avg_confidence >= Decimal(str(settings.cross_ref_promotion_threshold))
    )
    if qualifies:
        row.is_promoted = True
        await session.flush()
        return True
    return False


async def demote(session: AsyncSession, row: CrossRef, *, reason: Optional[str] = None) -> None:
    """Remove the promoted flag (used when a fast-path rule regresses)."""
    if not row.is_promoted:
        return
    row.is_promoted = False
    if reason:
        # Caller is expected to log this separately; we don't store reason
        # inline because the table is intentionally lean.
        pass
    await session.flush()


async def list_promoted(
    session: AsyncSession, vendor_id: Optional[uuid.UUID] = None
) -> list[CrossRef]:
    stmt = select(CrossRef).where(CrossRef.is_promoted.is_(True))
    if vendor_id is not None:
        stmt = stmt.where(CrossRef.vendor_id == vendor_id)
    result = await session.execute(stmt.order_by(CrossRef.last_seen_at.desc()))
    return list(result.scalars().all())

