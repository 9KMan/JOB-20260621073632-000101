"""FastAPI application entry point for the AP Automation Core Engine."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.router import api_v1_router
from api.schemas import HealthResponse
from core.config import get_settings
from core.database import dispose_engine, healthcheck

# Importing ``models`` registers every ORM class on Base.metadata so that
# Alembic autogenerate and ``create_all`` see them.
import models  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: nothing heavy on startup, dispose engine on shutdown."""
    settings = get_settings()
    logger.info(
        "Starting %s (env=%s, log_level=%s)",
        settings.app_name,
        settings.app_env,
        settings.log_level,
    )
    try:
        yield
    finally:
        await dispose_engine()
        logger.info("Shutdown complete")


app = FastAPI(
    title="AP Automation Core Engine",
    version="0.1.0",
    description="Three-way matching, ledger, and learning loop for AP automation.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


def _configure_middleware() -> None:
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        logger.info("%s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response


_configure_middleware()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "ap-automation-core", "version": app.version}


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    db_ok = await healthcheck()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db=db_ok,
        version=app.version,
    )


app.include_router(api_v1_router)
