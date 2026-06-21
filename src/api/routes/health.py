// src/api/routes/health.py
"""Health check endpoints."""
from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    database: str


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Check application and database health."""
    from src.app.config import get_settings
    from src.app.database import async_session_maker

    settings = get_settings()
    db_status = "unknown"

    try:
        async with async_session_maker() as session:
            await session.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        database=db_status
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict:
    """Check if the application is ready to accept traffic."""
    return {"ready": True}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict:
    """Check if the application is alive."""
    return {"alive": True}
