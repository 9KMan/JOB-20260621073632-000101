// src/app/main.py
"""FinaRo AP Automation Core Engine - FastAPI Application."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.config import get_settings
from src.app.database import close_db, init_db
from src.api import auth, delivery_notes, invoices, matches, purchase_orders
from src.api.health import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    FinaRo AP Automation Core Engine - 3-Way Matching System
    
    ## Features
    - **Purchase Orders**: Manage supplier POs
    - **Invoices**: Process incoming supplier invoices
    - **Delivery Notes**: Track deliveries against POs
    - **3-Way Matching**: Automated matching of Invoice × Delivery Note × Purchase Order
    - **Balance Resolution**: Track partial matches and balances
    
    ## Matching Layers
    1. **PO Anchoring**: PO as single source of truth
    2. **Cascade Matching**: Invoice↔PO, DN↔PO, Invoice↔DN
    3. **Balance Resolution**: Partial matches and multi-delivery support
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(
    purchase_orders.router, prefix="/api/v1/purchase-orders", tags=["Purchase Orders"]
)
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(
    delivery_notes.router, prefix="/api/v1/delivery-notes", tags=["Delivery Notes"]
)
app.include_router(matches.router, prefix="/api/v1/matches", tags=["Matching"])


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }
