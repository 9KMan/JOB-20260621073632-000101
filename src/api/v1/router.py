// src/api/v1/router.py
// src/api/v1/router.py
from fastapi import APIRouter

from src.api.v1 import (
    suppliers,
    purchase_orders,
    invoices,
    delivery_notes,
    matches,
    auth,
)

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(
    purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"]
)
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(
    delivery_notes.router, prefix="/delivery-notes", tags=["Delivery Notes"]
)
api_router.include_router(matches.router, prefix="/matches", tags=["Matching"])
