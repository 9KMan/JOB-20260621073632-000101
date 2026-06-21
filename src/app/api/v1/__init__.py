// src/app/api/v1/__init__.py
"""API v1 routes package."""

from fastapi import APIRouter

from src.app.api.v1 import (
    suppliers,
    purchase_orders,
    delivery_notes,
    invoices,
    matching
)

router = APIRouter(prefix="/api/v1")

router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
router.include_router(delivery_notes.router, prefix="/delivery-notes", tags=["Delivery Notes"])
router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
router.include_router(matching.router, prefix="/matching", tags=["Matching"])

__all__ = ["router"]
