# api/v1/router.py
"""Aggregated API v1 router — combines all domain routers."""

from fastapi import APIRouter

from api.v1 import invoices, purchase_orders, delivery_notes, matching, exceptions

api_router = APIRouter()

# Invoice endpoints
api_router.include_router(
    invoices.router,
    prefix="/invoices",
    tags=["Invoices"],
)

# Purchase Order endpoints
api_router.include_router(
    purchase_orders.router,
    prefix="/purchase-orders",
    tags=["Purchase Orders"],
)

# Delivery Note endpoints
api_router.include_router(
    delivery_notes.router,
    prefix="/delivery-notes",
    tags=["Delivery Notes"],
)

# Matching Engine endpoints
api_router.include_router(
    matching.router,
    prefix="/matching",
    tags=["Matching Engine"],
)

# Exception endpoints
api_router.include_router(
    exceptions.router,
    prefix="/exceptions",
    tags=["Exceptions"],
)
