python
// tests/integration/test_matching_flow.py
"""Full matching flow integration test.

Exercises the public API surface: ingest a PO, ingest an invoice that matches
that PO line-for-line, run the matching cascade, and verify the decision.
Uses an in-memory SQLite database via SQLAlchemy so the test does not require
a live Postgres instance; the matching engine is DB-agnostic.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///:memory:")


@pytest.mark.asyncio
async def test_matching_flow_end_to_end():
    from core.config import get_settings
    from models import Base
    from main import app  # imported lazily so settings env is honored first

    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Override the app's get_session to use our in-memory engine.
    from core.database import get_session

    async def _override_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        vendor_id = uuid.uuid4()

        # 1. Ingest a purchase order.
        po_payload = {
            "po_number": "PO-1000",
            "vendor_id": str(vendor_id),
            "vendor_name": "Acme Co.",
            "currency": "USD",
            "order_date": "2026-06-01",
            "total_amount": "99.90",
            "lines": [
                {
                    "line_number": 1,
                    "sku": "SKU-1",
                    "description": "Widget",
                    "ordered_qty": "10",
                    "unit_price": "9.99",
                    "line_total": "99.90",
                }
            ],
        }
        po_resp = await client.post("/api/v1/purchase-orders", json=po_payload)
        assert po_resp.status_code == 201, po_resp.text
        po_id = po_resp.json()["id"]

        # 2. Ingest an invoice that matches the PO exactly.
        invoice_payload = {
            "invoice_number": "INV-100",
            "vendor_id": str(vendor_id),
            "vendor_name": "Acme Co.",
            "currency": "USD",
            "invoice_date": "2026-06-21",
            "subtotal": "99.90",
            "tax_amount": "0",
            "total_amount": "99.90",
            "source": "manual",
            "is_ocr": False,
            "lines": [
                {
                    "line_number": 1,
                    "sku": "SKU-1",
                    "description": "Widget",
                    "quantity": "10",
                    "unit_price": "9.99",
                    "line_total": "99.90",
                }
            ],
        }
        inv_resp = await client.post("/api/v1/invoices", json=invoice_payload)
        assert inv_resp.status_code == 201, inv_resp.text
        invoice_id = inv_resp.json()["id"]

        # 3. Run the matching cascade.
        match_resp = await client.post(
            "/api/v1/matching/run",
            json={"invoice_id": invoice_id, "force": True},
        )
        assert match_resp.status_code == 200, match_resp.text
        body = match_resp.json()

        assert body["invoice_id"] == invoice_id
        assert body["overall_score"] >= 80.0
        assert len(body["line_decisions"]) == 1
        line_dec = body["line_decisions"][0]
        assert line_dec["purchase_order_line_id"] is not None
        assert line_dec["score"] >= 80.0
        assert line_dec["decision"] in {
            "auto_approve",
            "one_click_review",
            "needs_review",
            "exception",
            "rejected",
        }

    app.dependency_overrides.clear()
    await engine.dispose()

