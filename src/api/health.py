// src/api/health.py
"""Health check endpoint."""
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
