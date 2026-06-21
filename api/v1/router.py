# api/v1/router.py
"""API v1 router aggregator."""
from fastapi import APIRouter

from api.v1 import (
    invoices,
    purchase_orders,
    delivery_notes,
    matching,
    exceptions,
)

api_router = APIRouter()

# Include all versioned routers
api_router.include_router(
    invoices.router,
    prefix="/invoices",
    tags=["invoices"],
)
api_router.include_router(
    purchase_orders.router,
    prefix="/purchase-orders",
    tags=["purchase-orders"],
)
api_router.include_router(
    delivery_notes.router,
    prefix="/delivery-notes",
    tags=["delivery-notes"],
)
api_router.include_router(
    matching.router,
    prefix="/matching",
    tags=["matching"],
)
api_router.include_router(
    exceptions.router,
    prefix="/exceptions",
    tags=["exceptions"],
)
