// src/app/main.py
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.api.routes import auth, purchase_orders, invoices, delivery_notes, matches


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Dispose connection pool
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AP Automation Core Engine - 3-Way Matching System for Invoice, Delivery Note, and Purchase Order",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(
        purchase_orders.router, prefix="/api/v1/purchase-orders", tags=["Purchase Orders"]
    )
    app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
    app.include_router(
        delivery_notes.router, prefix="/api/v1/delivery-notes", tags=["Delivery Notes"]
    )
    app.include_router(matches.router, prefix="/api/v1/matches", tags=["Matching"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.app_name}

    return app


app = create_app()
