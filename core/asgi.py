# core/asgi.py
"""
FastAPI ASGI application entry point.

Configures the app, middleware, CORS, and routes.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import init_db, close_db, check_db_health
from api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AP Automation Core Engine — Invoice-to-PO Matching System for FinaRo",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # ── CORS Middleware ────────────────────────────────────────────────────────
    if settings.cors.is_allow_all:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allowed_origins,
            allow_credentials=settings.cors.allow_credentials,
            allow_methods=settings.cors.allowed_methods,
            allow_headers=settings.cors.allowed_headers,
        )

    # ── Request timing middleware ──────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        return response

    # ── Global exception handlers ──────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # In production, log the exception and return generic message
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"path": request.url.path} if settings.debug else {},
            },
        )

    # ── Health check endpoints ─────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy", "version": settings.app_version}

    @app.get("/health/ready", tags=["health"])
    async def readiness_check():
        """Readiness check including database connectivity."""
        db_health = await check_db_health()
        return {
            "status": "ready",
            "version": settings.app_version,
            "database": db_health,
        }

    # ── Include API router ─────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    return app


# Application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "core.asgi:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.server.log_level,
    )
