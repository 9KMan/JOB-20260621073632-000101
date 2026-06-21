// api/routes/__init__.py
"""API routes module."""
from fastapi import APIRouter

from api.routes.auth import router as auth_router
from api.routes.suppliers import router as suppliers_router
from api.routes.purchase_orders import router as purchase_orders_router
from api.routes.invoices import router as invoices_router
from api.routes.delivery_notes import router as delivery_notes_router
from api.routes.matching import router as matching_router
from api.routes.documents import router as documents_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(suppliers_router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(purchase_orders_router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(delivery_notes_router, prefix="/delivery-notes", tags=["Delivery Notes"])
api_router.include_router(matching_router, prefix="/matching", tags=["Matching"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
