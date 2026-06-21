// src/api/routes/health.py
"""Health check routes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "FinaRo AP Automation Engine",
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready"}
