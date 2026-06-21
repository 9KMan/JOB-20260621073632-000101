// src/api/v1/__init__.py
"""API v1 package."""
from fastapi import APIRouter

from src.api.v1.health import router as health_router
from src.api.v1.auth import router as auth_router
from src.api.v1.documents import router as documents_router
from src.api.v1.matching import router as matching_router

router = APIRouter()

router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(documents_router, prefix="/documents", tags=["Documents"])
router.include_router(matching_router, prefix="/matching", tags=["Matching"])
