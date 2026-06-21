# core/main.py
"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.router import api_router
from core.config import get_settings
from core.database import close_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="AP Automation Core Engine for Finaro - Invoice Matching and Processing",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors with consistent format."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict: Service health status
    """
    return {"status": "healthy", "service": settings.app_name}


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint.

    Returns:
        dict: Welcome message and API info
    """
    return {
        "message": "AP Automation Core Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")
