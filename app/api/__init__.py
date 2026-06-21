# app/api/__init__.py
"""API routes for FinaRo AP Automation Engine."""
from app.api.auth import router as auth_router
from app.api.vendors import router as vendors_router
from app.api.purchase_orders import router as purchase_orders_router
from app.api.invoices import router as invoices_router
from app.api.delivery_notes import router as delivery_notes_router
from app.api.matching import router as matching_router
from app.api.balances import router as balances_router

__all__ = [
    "auth_router",
    "vendors_router",
    "purchase_orders_router",
    "invoices_router",
    "delivery_notes_router",
    "matching_router",
    "balances_router",
]
