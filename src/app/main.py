// src/app/main.py
"""
FinaRo AP Automation Core Engine
Main FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    logger.info("application_startup", version=settings.VERSION, environment=settings.ENVIRONMENT)
    
    # Create database tables on startup (for development only)
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_tables_created")
    
    yield
    
    logger.info("application_shutdown")
    await engine.dispose()


app = FastAPI(
    title="FinaRo AP Automation Engine",
    description="3-Way Matching Engine for Invoice × Delivery Note × Purchase Order",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "version": settings.VERSION, "service": "finaro-ap-engine"}


# API v1 routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
