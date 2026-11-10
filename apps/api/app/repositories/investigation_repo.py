"""
Investigation Repository
Handles storage, retrieval, results aggregation, and deletion of investigations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from apps.api.app.models import (
    Investigation,
    Profile,
    Evidence,
    Relationship,
    SearchInput,
    AuditEvent,
)
from packages.schemas import SearchResult, VerificationStatus


class InvestigationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        target_value: str,
        search_type: str = "username",
        user_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Investigation:
        options_str = json.dumps(options or {})
        inv = Investigation(
            target_value=target_value.strip(),
            search_type=search_type,
            user_id=user_id,
            status="queued",
            options_json=options_str,
        )
        self.db.add(inv)
        await self.db.flush()

        # Add search input record
        s_input = SearchInput(
            investigation_id=inv.id,
            encrypted_value=target_value.strip(),
            input_type=search_type,
        )
        self.db.add(s_input)

        # Audit event
        audit = AuditEvent(
            user_id=user_id,
            investigation_id=inv.id,
            action="investigation_created",
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(inv)
        return inv

    async def get_by_id(self, investigation_id: str) -> Optional[Investigation]:
        stmt = (
            select(Investigation)
            .where(Investigation.id == investigation_id, Investigation.deleted_at.is_(None))
            .options(
                selectinload(Investigation.profiles).selectinload(Profile.evidence_records),
                selectinload(Investigation.relationships),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Investigation]:
        stmt = select(Investigation).where(Investigation.deleted_at.is_(None))
        if user_id:
            stmt = stmt.where(Investigation.user_id == user_id)
        else:
            # Unauthenticated/guest callers only see anonymous investigations
            stmt = stmt.where(Investigation.user_id.is_(None))
        stmt = stmt.order_by(Investigation.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        investigation_id: str,
        status: str,
        total_sites_checked: Optional[int] = None,
        verified_count: Optional[int] = None,
        inconclusive_count: Optional[int] = None,
        completed: bool = False,
    ) -> None:
        values: Dict[str, Any] = {"status": status}
        if total_sites_checked is not None:
            values["total_sites_checked"] = total_sites_checked
        if verified_count is not None:
            values["verified_count"] = verified_count
        if inconclusive_count is not None:
            values["inconclusive_count"] = inconclusive_count
        if completed:
            values["completed_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(Investigation).where(Investigation.id == investigation_id).values(**values)
        )
        await self.db.commit()

    async def record_search_result(
        self,
        investigation_id: str,
        result: SearchResult,
    ) -> Optional[Profile]:
        """
        Persists a SearchResult, storing Profile and Evidence records if verified or unverified.
        """
        # Strictly persist only confirmed VERIFIED profiles to eliminate false positives
        if result.status != VerificationStatus.VERIFIED:
            return None

        p_data = result.profile
        if not p_data:
            return None

        profile = Profile(
            investigation_id=investigation_id,
            platform=p_data.platform,
            category=p_data.category.value if hasattr(p_data.category, "value") else str(p_data.category),
            username=p_data.username,
            profile_url=p_data.profile_url,
            display_name=p_data.display_name,
            biography=p_data.biography,
            public_website=p_data.public_website,
            profile_image_url=p_data.profile_image_url,
            location=p_data.location,
            confidence_existence=p_data.confidence_existence,
            confidence_data=p_data.confidence_data,
            identity_confidence=p_data.identity_confidence,
        )
        self.db.add(profile)
        await self.db.flush()

        if result.evidence:
            ev = result.evidence
            evidence = Evidence(
                profile_id=profile.id,
                source_url=ev.source_url,
                evidence_type=ev.evidence_type,
                detection_method=ev.detection_method.value if hasattr(ev.detection_method, "value") else str(ev.detection_method),
                verification_status=ev.verification_status.value if hasattr(ev.verification_status, "value") else str(ev.verification_status),
                confidence_score=ev.confidence_score,
                adapter_version=ev.adapter_version,
                observed_at=ev.observed_at,
                match_evidence=ev.match_evidence,
                raw_data_json=json.dumps(ev.raw_details or {}),
            )
            self.db.add(evidence)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def save_relationships(
        self,
        investigation_id: str,
        relationships: List[Any],
    ) -> None:
        for r in relationships:
            rel = Relationship(
                investigation_id=investigation_id,
                source_profile_id=r.source,
                target_profile_id=r.target,
                relationship_type=r.relationship_type,
                confidence_tier=r.confidence_tier,
                confidence_score=r.confidence_score,
                evidence_reason=r.evidence_reason,
            )
            self.db.add(rel)
        await self.db.commit()

    async def soft_delete(self, investigation_id: str) -> bool:
        inv = await self.get_by_id(investigation_id)
        if not inv:
            return False
        inv.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

