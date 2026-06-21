// src/api/v1/__init__.py
"""API v1 package."""
from fastapi import APIRouter

from src.api.v1.routes import (
    auth,
    users,
    vendors,
    purchase_orders,
    invoices,
    delivery_notes,
    matches,
    balances,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(delivery_notes.router, prefix="/delivery-notes", tags=["Delivery Notes"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(balances.router, prefix="/balances", tags=["Balances"])
