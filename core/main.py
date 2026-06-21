// core/main.py
"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.router import api_router
from core.config import settings
from core.database import check_database_connection, close_database, init_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    await init_database()
    yield
    # Shutdown
    await close_database()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AP Automation Core Engine for Finaro - Invoice matching and processing",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle validation errors with custom response format."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring."""
    db_healthy = await check_database_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": settings.app_version,
        "database": "connected" if db_healthy else "disconnected",
    }


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """Root endpoint returning API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "core.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
    )
