"""
Investigation Orchestration Service
Coordinates execution of username intelligence investigations.
Updates progress, executes concurrent probes, resolves identity relationships, and handles background execution.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database.session import AsyncSessionLocal
from apps.api.app.repositories.investigation_repo import InvestigationRepository
from packages.schemas import (
    PlatformCategory,
    VerificationStatus,
    ProfileData,
)
from packages.osint_engine.adapters.curated_adapter import CuratedOSINTAdapter
from packages.osint_engine.core.identity_resolver import IdentityResolver, InvestigationGraph

logger = logging.getLogger("opentrace.service")


class InvestigationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InvestigationRepository(db)
        self.adapter = CuratedOSINTAdapter()

    async def create_investigation(
        self,
        target_value: str,
        search_type: str = "username",
        user_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        return await self.repo.create(
            target_value=target_value,
            search_type=search_type,
            user_id=user_id,
            options=options,
        )

    @classmethod
    async def run_investigation_job(
        cls,
        investigation_id: str,
        target_username: str,
        categories: Optional[List[PlatformCategory]] = None,
        concurrency: int = 15,
    ) -> None:
        """
        Background task worker that executes the investigation end-to-end.
        Runs using isolated database session so background tasks never collide.
        """
        async with AsyncSessionLocal() as session:
            repo = InvestigationRepository(session)
            adapter = CuratedOSINTAdapter()

            try:
                await repo.update_status(investigation_id, status="searching")

                total_checked = 0
                verified_count = 0
                inconclusive_count = 0
                discovered_profiles: List[ProfileData] = []

                async for result in adapter.search_username(
                    username=target_username,
                    categories=categories,
                    concurrency=concurrency,
                ):
                    total_checked += 1
                    if result.status == VerificationStatus.VERIFIED:
                        verified_count += 1
                        if result.profile:
                            discovered_profiles.append(result.profile)
                    elif result.status in (VerificationStatus.INCONCLUSIVE, VerificationStatus.ERROR):
                        inconclusive_count += 1

                    # Persist profile and evidence if verified/unverified
                    await repo.record_search_result(investigation_id, result)

                    # Update progress every 2 sites
                    if total_checked % 2 == 0:
                        await repo.update_status(
                            investigation_id,
                            status="searching",
                            total_sites_checked=total_checked,
                            verified_count=verified_count,
                            inconclusive_count=inconclusive_count,
                        )

                # 4. Identity Resolution: correlate discovered profiles into an evidence graph
                if discovered_profiles:
                    graph: InvestigationGraph = IdentityResolver.resolve_relationships(
                        target_username=target_username,
                        profiles=discovered_profiles,
                    )
                    await repo.save_relationships(investigation_id, graph.edges)

                # Mark investigation completed
                await repo.update_status(
                    investigation_id,
                    status="completed",
                    total_sites_checked=total_checked,
                    verified_count=verified_count,
                    inconclusive_count=inconclusive_count,
                    completed=True,
                )

            except Exception as e:
                logger.error(f"Investigation {investigation_id} failed: {e}", exc_info=True)
                await repo.update_status(investigation_id, status="failed", completed=True)

    async def get_graph(self, investigation_id: str) -> Optional[InvestigationGraph]:
        inv = await self.repo.get_by_id(investigation_id)
        if not inv:
            return None

        profiles_data = [
            ProfileData(
                platform=p.platform,
                username=p.username,
                profile_url=p.profile_url,
                category=PlatformCategory(p.category) if p.category in [c.value for c in PlatformCategory] else PlatformCategory.OTHER,
                display_name=p.display_name,
                biography=p.biography,
                public_website=p.public_website,
                profile_image_url=p.profile_image_url,
                location=p.location,
                confidence_existence=p.confidence_existence,
                confidence_data=p.confidence_data,
                identity_confidence=p.identity_confidence,
            )
            for p in inv.profiles
        ]

        return IdentityResolver.resolve_relationships(
            target_username=inv.target_value,
            profiles=profiles_data,
        )

