# core/main.py
"""FastAPI application entry point — AP Automation Core Engine."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import close_db, init_db
from api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle — startup and shutdown."""
    # Startup
    if not settings.is_production:
        await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description=(
        "AP Automation Core Engine — Invoice, PO, and Delivery Note matching "
        "with automated decision routing."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately per environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests."""
    import logging
    import time

    logger = logging.getLogger("ap_engine.http")
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %d %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging

    logger = logging.getLogger("ap_engine")
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness/readiness probe."""
    return {"status": "healthy", "environment": settings.environment}


@app.get("/ready", tags=["health"])
async def readiness_check() -> dict[str, str]:
    """Readiness check — verifies database connectivity."""
    from sqlalchemy import text

    from core.database import get_engine

    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": str(e)},
        )


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(api_v1_router, prefix="/api/v1")
