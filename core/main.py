# core/main.py
"""
FastAPI application entry point.

Main application factory with middleware, routes, and lifecycle management.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.router import api_router
from core.config import settings
from core.database import close_db, db_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {app.title} in {settings.environment} mode")
    logger.info("Initializing database connection pool...")
    
    try:
        # Verify database connectivity
        is_connected = await db_manager.ensure_connectivity()
        if is_connected:
            logger.info("Database connection verified")
        else:
            logger.warning("Database connection could not be verified - continuing anyway")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns a fully configured application instance.
    """
    app = FastAPI(
        title="AP Automation Core Engine",
        description="Accounts Payable Automation Matching Engine for FinaRo",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # CORS Middleware
    # ─────────────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Exception Handlers
    # ─────────────────────────────────────────────────────────────────────────
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions."""
        logger.warning(f"ValueError: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Health Check Endpoint
    # ─────────────────────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check() -> Dict[str, Any]:
        """
        Health check endpoint for load balancers and container orchestration.
        
        Returns database connectivity status.
        """
        db_healthy = await db_manager.ensure_connectivity()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "environment": settings.environment,
            "database": "connected" if db_healthy else "disconnected",
            "version": "0.1.0",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Root Endpoint
    # ─────────────────────────────────────────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root() -> Dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": "AP Automation Core Engine",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Include API Routes
    # ─────────────────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    return app


# Create application instance
app = create_app()
