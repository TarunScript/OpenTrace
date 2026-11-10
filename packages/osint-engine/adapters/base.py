"""
Standardized OSINT Adapter Interface
Ensures modularity: search engines and data sources can be swapped, extended, or mocked without altering the API.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Dict, Any
from packages.schemas import SearchResult, SiteDefinition, PlatformCategory


class BaseOSINTAdapter(ABC):
    """
    Abstract base class for all username footprint search adapters.
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    @abstractmethod
    async def check_site(self, site: SiteDefinition, username: str) -> SearchResult:
        """
        Executes a targeted investigation check against a single site definition.
        """
        pass

    @abstractmethod
    async def search_username(
        self,
        username: str,
        categories: Optional[List[PlatformCategory]] = None,
        concurrency: int = 15,
        timeout_seconds: float = 8.0,
    ) -> AsyncIterator[SearchResult]:
        """
        Asynchronously streams SearchResult items as each platform finishes checking.
        """
        pass

    @abstractmethod
    def supported_sites(self) -> List[SiteDefinition]:
        """
        Returns the list of site definitions supported by this adapter.
        """
        pass

