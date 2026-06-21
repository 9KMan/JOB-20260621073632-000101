# src/app/main.py
"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.api.v1.router import api_router
from src.app.config import settings
from src.app.database import engine, Base
from src.app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    setup_logging()
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## FinaRo AP Automation Core Engine
    
    A 3-Way Matching Engine for Accounts Payable automation.
    
    ### Features:
    - **Purchase Order (PO) Management** - Single source of truth for anchoring
    - **Invoice Processing** - Automated invoice validation and matching
    - **Delivery Note Tracking** - DN matching with PO and Invoice
    - **3-Way Matching Engine** - Automated matching with confidence scoring
    - **Balance Resolution** - Partial match and balance tracking
    - **Decision Routing** - Auto-approve, human review, or dispute workflows
    """,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)


# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    response = await call_next(request)
    
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        }
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "type": type(exc).__name__,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get(f"{settings.API_V1_PREFIX}/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": settings.API_VERSION,
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
