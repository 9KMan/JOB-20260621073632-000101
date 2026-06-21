# api/v1/router.py
"""API v1 router — aggregates all domain routers."""

from fastapi import APIRouter

from api.v1 import (
    invoices,
    purchase_orders,
    delivery_notes,
    matching,
    exceptions,
)

api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Mount sub-routers
api_v1_router.include_router(
    invoices.router,
    prefix="/invoices",
    tags=["invoices"],
)
api_v1_router.include_router(
    purchase_orders.router,
    prefix="/purchase-orders",
    tags=["purchase-orders"],
)
api_v1_router.include_router(
    delivery_notes.router,
    prefix="/delivery-notes",
    tags=["delivery-notes"],
)
api_v1_router.include_router(
    matching.router,
    prefix="/matching",
    tags=["matching"],
)
api_v1_router.include_router(
    exceptions.router,
    prefix="/exceptions",
    tags=["exceptions"],
)
