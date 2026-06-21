"""Aggregator that mounts every v1 sub-router under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from api.v1 import delivery_notes, exceptions, invoices, matching, purchase_orders

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_v1_router.include_router(
    purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"]
)
api_v1_router.include_router(
    delivery_notes.router, prefix="/delivery-notes", tags=["delivery-notes"]
)
api_v1_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_v1_router.include_router(exceptions.router, prefix="/exceptions", tags=["exceptions"])

__all__ = ["api_v1_router"]
