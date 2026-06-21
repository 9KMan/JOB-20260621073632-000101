// app/main.py
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine

# Import routers
from api.routes import auth, invoices, delivery_notes, purchase_orders, matching

settings = get_settings()

# Create tables (for development; in production use migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AP Automation Core Engine — 3-Way Matching (Invoice × Delivery Note × Purchase Order)",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(purchase_orders.router, prefix="/api/v1/purchase-orders", tags=["Purchase Orders"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(delivery_notes.router, prefix="/api/v1/delivery-notes", tags=["Delivery Notes"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
