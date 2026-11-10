"""
Sites Directory Endpoint
"""
from typing import List, Optional
from fastapi import APIRouter, Query
from packages.site_registry.registry import default_registry
from packages.schemas import PlatformCategory
from apps.api.app.schemas import SiteResponse

router = APIRouter(prefix="/sites", tags=["Site Registry"])


@router.get("", response_model=List[SiteResponse])
async def list_sites(category: Optional[PlatformCategory] = Query(None)):
    """
    Returns curated supported websites for digital footprint investigations.
    """
    sites = default_registry.list_all(category=category)
    return [
        SiteResponse(
            name=s.name,
            category=s.category.value,
            url_pattern=s.url_pattern,
            check_type=s.check_type.value,
            is_active=s.is_active,
        )
        for s in sites
    ]

