# src/app/main.py
"""
FinaRo AP Automation Core Engine - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.config import get_settings
from src.app.database import init_db, close_db
from src.app.api.v1 import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    FinaRo AP Automation Core Engine
    
    A 3-Way Matching Engine for Invoice × Delivery Note × Purchase Order reconciliation.
    
    ## Features
    - **Layer 1 - PO Anchoring**: Establish deterministic anchors using Purchase Orders
    - **Layer 2 - Cascade Matching**: Match documents with weighted scoring
    - **Layer 3 - Balance Resolution**: Track partial matches and balances
    - **Decision Routing**: CONFIRMED → AUTO-APPROVE, PENDING → HUMAN_REVIEW, REJECTED → DISPUTE
    
    ## Authentication
    JWT-based authentication with HS256 algorithm.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
            "detail": "An internal server error occurred",
            "type": type(exc).__name__,
        },
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to FinaRo AP Automation Core Engine",
        "docs": "/docs",
        "health": "/health",
    }
