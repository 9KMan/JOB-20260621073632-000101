// src/app/api/v1/router.py
"""Main API v1 router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.v1 import auth, users, suppliers, purchase_orders, invoices, delivery_notes, matches, balances

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(delivery_notes.router, prefix="/delivery-notes", tags=["Delivery Notes"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(balances.router, prefix="/balances", tags=["Balances"])
