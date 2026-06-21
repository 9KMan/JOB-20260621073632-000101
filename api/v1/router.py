# api/v1/router.py
"""API v1 router aggregator.

Combines all v1 endpoint routers into a single router.
"""

from fastapi import APIRouter

from api.v1 import (
    delivery_notes,
    exceptions,
    invoices,
    matching,
    purchase_orders,
)

api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(
    invoices.router,
    prefix="/invoices",
    tags=["Invoices"],
)
api_router.include_router(
    purchase_orders.router,
    prefix="/purchase-orders",
    tags=["Purchase Orders"],
)
api_router.include_router(
    delivery_notes.router,
    prefix="/delivery-notes",
    tags=["Delivery Notes"],
)
api_router.include_router(
    matching.router,
    prefix="/matching",
    tags=["Matching"],
)
api_router.include_router(
    exceptions.router,
    prefix="/exceptions",
    tags=["Exceptions"],
)
