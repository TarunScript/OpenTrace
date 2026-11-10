"""
Audit Script: Test persistence of investigations across restarts.
Simulates backend restart and verifies database retention.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.api.app.config import settings
from apps.api.app.models import Base
from apps.api.app.repositories.investigation_repo import InvestigationRepository
from packages.schemas import SearchResult, ProfileData, PlatformCategory, VerificationStatus, EvidenceModel, DetectionMethod


import pytest

@pytest.mark.asyncio
async def test_persistence():
    db_url = settings.DATABASE_URL
    print(f"Testing persistence with DB: {db_url}")

    # Process 1: Create and populate
    engine1 = create_async_engine(db_url)
    session_factory1 = async_sessionmaker(bind=engine1, class_=AsyncSession, expire_on_commit=False)

    async with engine1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inv_id = None
    async with session_factory1() as session1:
        repo1 = InvestigationRepository(session1)
        inv = await repo1.create("persist_test_user", search_type="username")
        inv_id = inv.id
        print(f"Created investigation: {inv_id}")

        # Add profile
        p_data = ProfileData(
            platform="GitHub",
            username="persist_test_user",
            profile_url="https://github.com/persist_test_user",
            category=PlatformCategory.DEVELOPER,
            display_name="Persistence Tester",
            confidence_existence=0.95,
            confidence_data=0.90,
        )
        ev_data = EvidenceModel(
            source_url="https://github.com/persist_test_user",
            detection_method=DetectionMethod.COMPOSITE,
            verification_status=VerificationStatus.VERIFIED,
            confidence_score=0.95,
            match_evidence="Profile structure verified.",
        )
        sr = SearchResult(
            site_name="GitHub",
            category=PlatformCategory.DEVELOPER,
            target_username="persist_test_user",
            status=VerificationStatus.VERIFIED,
            profile=p_data,
            evidence=ev_data,
        )
        await repo1.record_search_result(inv_id, sr)
        await repo1.update_status(inv_id, status="completed", total_sites_checked=1, verified_count=1, completed=True)

    # Completely dispose first engine (simulating shutdown/restart)
    await engine1.dispose()
    print("Backend 1 stopped, connections disposed.")

    # Process 2: Connect fresh
    engine2 = create_async_engine(db_url)
    session_factory2 = async_sessionmaker(bind=engine2, class_=AsyncSession, expire_on_commit=False)

    async with session_factory2() as session2:
        repo2 = InvestigationRepository(session2)
        loaded = await repo2.get_by_id(inv_id)
        assert loaded is not None, "Investigation disappeared after restart!"
        assert loaded.target_value == "persist_test_user"
        assert loaded.status == "completed"
        assert len(loaded.profiles) == 1
        p = loaded.profiles[0]
        assert p.platform == "GitHub"
        assert p.display_name == "Persistence Tester"
        assert len(p.evidence_records) == 1
        print(f"SUCCESS: Loaded investigation #{inv_id} with {len(loaded.profiles)} profiles and {len(p.evidence_records)} evidence records after simulated restart!")

    await engine2.dispose()


if __name__ == "__main__":
    asyncio.run(test_persistence())
