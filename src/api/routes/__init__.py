// src/api/routes/__init__.py
"""API routes module."""
from fastapi import APIRouter

from src.api.routes import documents, health, matching

router = APIRouter()
router.include_router(health.router)
router.include_router(documents.router)
router.include_router(matching.router)
