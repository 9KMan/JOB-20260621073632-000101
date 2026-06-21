"""Shared pytest fixtures.

These fixtures intentionally avoid requiring a live PostgreSQL connection.
The async engine used by the application can be replaced with an in-memory
SQLite database for unit tests via ``_override_engine``.
"""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import AsyncIterator

import pytest
import pytest_asyncio


def _ensure_test_env() -> None:
    """Set the minimum env vars required by Settings before any import."""
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
    os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost/test")
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-1234567890")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("APP_ENV", "test")


_ensure_test_env()


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Reset the lru_cache on get_settings between tests."""
    from core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings():
    from core.config import get_settings

    return get_settings()


@pytest.fixture
def vendor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def today() -> date:
    return date(2026, 6, 21)


@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def invoice_factory(vendor_id, today):
    """Lightweight factory that builds an in-memory Invoice (not yet persisted)."""

    from models.enums import DocumentStatus
    from models.invoice import Invoice, InvoiceLine

    def _make(
        *,
        invoice_number: str = "INV-100",
        lines: list[InvoiceLine] | None = None,
        total: Decimal | None = None,
        vendor_name: str = "Acme Co.",
        currency: str = "USD",
    ) -> Invoice:
        inv = Invoice(
            invoice_number=invoice_number,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            currency=currency,
            invoice_date=today,
            received_at=datetime.now(timezone.utc),
            subtotal=Decimal("0"),
            tax_amount=Decimal("0"),
            total_amount=total or Decimal("0"),
            status=DocumentStatus.INGESTED,
            source="manual",
            is_ocr=False,
        )
        for line in lines or []:
            inv.lines.append(line)
        return inv

    return _make


@pytest.fixture
def invoice_line_factory():
    """Builds unsaved InvoiceLine rows for use in factory/fixture composition."""

    from models.invoice import InvoiceLine

    def _make(
        *,
        line_number: int = 1,
        sku: str | None = "SKU-1",
        description: str = "Widget",
        quantity: Decimal = Decimal("10"),
        unit_price: Decimal = Decimal("9.99"),
        line_total: Decimal | None = None,
    ) -> InvoiceLine:
        return InvoiceLine(
            line_number=line_number,
            sku=sku,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total if line_total is not None else quantity * unit_price,
            uom="EA",
            tax_amount=Decimal("0"),
        )

    return _make


@pytest.fixture
def po_line_factory():
    from models.purchase_order import PurchaseOrderLine

    def _make(
        *,
        line_number: int = 1,
        sku: str | None = "SKU-1",
        description: str = "Widget",
        ordered_qty: Decimal = Decimal("10"),
        unit_price: Decimal = Decimal("9.99"),
        line_total: Decimal | None = None,
        purchase_order_id: uuid.UUID | None = None,
    ) -> PurchaseOrderLine:
        if purchase_order_id is None:
            purchase_order_id = uuid.uuid4()
        return PurchaseOrderLine(
            purchase_order_id=purchase_order_id,
            line_number=line_number,
            sku=sku,
            description=description,
            ordered_qty=ordered_qty,
            received_qty=Decimal("0"),
            invoiced_qty=Decimal("0"),
            unit_price=unit_price,
            line_total=line_total if line_total is not None else ordered_qty * unit_price,
            uom="EA",
        )

    return _make


@pytest_asyncio.fixture
async def fake_session() -> AsyncIterator[object]:
    """Stub AsyncSession for unit tests.

    Tests that exercise DB I/O should mark themselves as integration tests and
    override this fixture with one backed by an aiosqlite / pg test instance.
    """
    yield object()
