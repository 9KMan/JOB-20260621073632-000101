// api/v1/__init__.py
"""API v1 package.

This package contains versioned API routes:
- invoices.py: Invoice endpoints
- purchase_orders.py: PO endpoints
- delivery_notes.py: Delivery note endpoints
- matching.py: Matching engine endpoints
- exceptions.py: Exception handling endpoints
"""

from api.v1.router import api_router

__all__ = ["api_router"]
