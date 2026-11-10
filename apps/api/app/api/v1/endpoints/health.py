"""
Health Check Endpoint
"""
from fastapi import APIRouter
from packages.site_registry.registry import default_registry
from apps.api.app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "supported_sites_count": default_registry.count(),
        "engine": "CuratedOSINTAdapter",
    }

