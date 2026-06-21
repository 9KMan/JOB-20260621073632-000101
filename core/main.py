// core/main.py
"""FastAPI application entry point.

This module creates and configures the FastAPI application with:
- API routers
- Middleware (CORS, logging, error handling)
- Health check endpoint
- OpenAPI documentation
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.router import api_router
from core.config import settings
from core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connection
    - Shutdown: Close database connections
    """
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    yield
    # Shutdown
    print("Shutting down application...")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url=settings.docs_url if settings.environment != "production" else None,
        redoc_url=settings.redoc_url if settings.environment != "production" else None,
        openapi_url=settings.openapi_url if settings.environment != "production" else None,
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Register API router
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint.

        Returns:
            dict: Health status and application info
        """
        from core.database import health_check as db_health_check

        db_healthy = await db_health_check()

        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "database": "connected" if db_healthy else "disconnected",
        }

    # Global exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle request validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "message": str(exc) if settings.debug else "An unexpected error occurred",
            },
        )

    return app


# Create application instance
app = create_app()
