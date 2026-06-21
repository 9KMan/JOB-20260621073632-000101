// src/app/api/__init__.py
"""API routes."""
from app.api.auth import router as auth_router
from app.api.purchase_orders import router as po_router
from app.api.invoices import router as invoice_router
from app.api.delivery_notes import router as dn_router
from app.api.matches import router as match_router

__all__ = [
    "auth_router",
    "po_router",
    "invoice_router",
    "dn_router",
    "match_router",
]
