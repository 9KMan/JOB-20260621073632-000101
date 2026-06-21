# src/app/main.py
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.config import settings
from src.app.database import engine, Base
from src.api import auth, purchase_orders, invoices, delivery_notes, matches, balances


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AP Automation Core Engine — 3-Way Matching (Invoice × Delivery Note × PO)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
        },
    )


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


# API Routes
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(purchase_orders.router, prefix=f"{settings.api_v1_prefix}/purchase-orders", tags=["Purchase Orders"])
app.include_router(invoices.router, prefix=f"{settings.api_v1_prefix}/invoices", tags=["Invoices"])
app.include_router(delivery_notes.router, prefix=f"{settings.api_v1_prefix}/delivery-notes", tags=["Delivery Notes"])
app.include_router(matches.router, prefix=f"{settings.api_v1_prefix}/matches", tags=["Matching"])
app.include_router(balances.router, prefix=f"{settings.api_v1_prefix}/balances", tags=["Balances"])
