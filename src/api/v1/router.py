// src/api/v1/router.py
"""API v1 router - aggregates all endpoints."""
from fastapi import APIRouter

from src.api.v1.endpoints import (
    purchase_orders,
    invoices,
    delivery_notes,
    matches,
    balances,
)

api_router = APIRouter()

api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(delivery_notes.router, prefix="/delivery-notes", tags=["Delivery Notes"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(balances.router, prefix="/balances", tags=["Balances"])
