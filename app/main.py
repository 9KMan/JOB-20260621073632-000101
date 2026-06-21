# app/main.py
"""FastAPI Application Entry Point for FinaRo AP Automation Engine."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time

from app.config import settings
from app.database import engine, Base
from app.api import (
    vendors_router,
    purchase_orders_router,
    invoices_router,
    delivery_notes_router,
    matching_router,
    balances_router,
    auth_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting FinaRo AP Automation Engine...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down FinaRo AP Automation Engine...")
    await engine.dispose()


app = FastAPI(
    title="FinaRo AP Automation Core Engine",
    description="3-Way Matching Engine for Invoice × Delivery Note × Purchase Order",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing."""
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"
    
    logger.info(
        f"Request started: {request.method} {request.url.path} "
        f"[request_id={request_id}]"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} duration={process_time:.3f}s "
            f"[request_id={request_id}]"
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"error={str(e)} duration={process_time:.3f}s "
            f"[request_id={request_id}]"
        )
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with consistent format."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(vendors_router, prefix="/api/v1/vendors", tags=["Vendors"])
app.include_router(
    purchase_orders_router, prefix="/api/v1/purchase-orders", tags=["Purchase Orders"]
)
app.include_router(invoices_router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(
    delivery_notes_router, prefix="/api/v1/delivery-notes", tags=["Delivery Notes"]
)
app.include_router(matching_router, prefix="/api/v1/matching", tags=["Matching"])
app.include_router(balances_router, prefix="/api/v1/balances", tags=["Balances"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": "FinaRo AP Automation Engine",
        "version": "1.0.0",
    }


@app.get("/api/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not ready", "database": "disconnected"}
