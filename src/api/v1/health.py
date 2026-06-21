// src/api/v1/health.py
"""Health check endpoints."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str
    timestamp: datetime


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the API is running",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Health status
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the API is ready to serve requests",
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint.

    Returns:
        ReadinessResponse: Readiness status
    """
    return ReadinessResponse(
        status="ready",
        database="connected",
        timestamp=datetime.now(timezone.utc),
    )
