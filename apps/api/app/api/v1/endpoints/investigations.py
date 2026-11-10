"""
Investigation Management Endpoints
"""
import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.config import settings
from apps.api.app.database.session import get_db
from apps.api.app.models import User
from apps.api.app.core.security import get_optional_current_user
from apps.api.app.services.investigation_service import InvestigationService
from apps.api.app.schemas import (
    InvestigationCreate,
    InvestigationSummary,
    InvestigationResultsResponse,
    ProfileResponse,
    EvidenceResponse,
)

logger = logging.getLogger("opentrace.api")
router = APIRouter(prefix="/investigations", tags=["Investigations"])


def check_investigation_access(inv, current_user: Optional[User], require_modify: bool = False):
    """
    Enforces per-user investigation authorization.
    Registered user investigations can only be accessed or modified by their owner.
    """
    if inv.user_id is not None:
        if not current_user or current_user.id != inv.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access or modify this investigation.",
            )
    elif require_modify and not current_user:
        # Anonymous investigations cannot be deleted by unauthenticated callers
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required to delete investigations.",
        )


@router.post("", response_model=InvestigationSummary, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    payload: InvestigationCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates a new digital footprint investigation across supported public sources.
    Dispatches to Celery worker when configured, or in-process background worker.
    """
    clean_value = payload.value.strip().lstrip("@")
    if not clean_value:
        raise HTTPException(status_code=400, detail="Target search input cannot be empty.")

    service = InvestigationService(db)
    options_dict = payload.options.model_dump() if payload.options else {}

    inv = await service.create_investigation(
        target_value=clean_value,
        search_type=payload.type,
        user_id=current_user.id if current_user else None,
        options=options_dict,
    )

    categories = payload.options.categories if payload.options else None

    # Dispatch to Celery worker if configured, with explicit observable fallback
    dispatched = False
    if settings.USE_CELERY:
        try:
            from services.worker.tasks.search_tasks import execute_investigation
            execute_investigation.delay(
                investigation_id=inv.id,
                target_username=clean_value,
                categories=categories,
            )
            dispatched = True
            logger.info(f"Dispatched investigation {inv.id} to Celery worker")
        except Exception as celery_err:
            logger.error(
                f"[PRODUCTION ALERT] Celery broker/worker unreachable ({celery_err}). "
                f"Falling back to in-process execution for investigation {inv.id}. "
                "Production infrastructure requires attention."
            )
            # Do not silently mask: record visible diagnostic event in options
            options_dict["execution_mode"] = "fallback_in_process"
            options_dict["celery_dispatch_error"] = str(celery_err)
            inv.options_json = str(options_dict)
            await db.commit()

    if not dispatched:
        background_tasks.add_task(
            InvestigationService.run_investigation_job,
            investigation_id=inv.id,
            target_username=clean_value,
            categories=categories,
        )

    return inv


@router.get("", response_model=List[InvestigationSummary])
async def list_investigations(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves investigation history. If authenticated, filters by user; otherwise returns recent guest investigations.
    """
    service = InvestigationService(db)
    user_id = current_user.id if current_user else None
    investigations = await service.repo.list_for_user(user_id=user_id)
    return investigations


@router.get("/{id}", response_model=InvestigationSummary)
async def get_investigation_status(
    id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the live status, progress, and metric counters of an investigation.
    """
    service = InvestigationService(db)
    inv = await service.repo.get_by_id(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    check_investigation_access(inv, current_user, require_modify=False)
    return inv


@router.get("/{id}/results", response_model=InvestigationResultsResponse)
async def get_investigation_results(
    id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns full investigation findings, including discovered profiles, evidence, and confidence scores.
    """
    service = InvestigationService(db)
    inv = await service.repo.get_by_id(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    check_investigation_access(inv, current_user, require_modify=False)

    profile_responses = []
    category_counts: dict = {}

    for p in inv.profiles:
        evidence_list = [
            EvidenceResponse(
                id=ev.id,
                source_url=ev.source_url,
                evidence_type=ev.evidence_type,
                detection_method=ev.detection_method,
                verification_status=ev.verification_status,
                confidence_score=ev.confidence_score,
                observed_at=ev.observed_at,
                match_evidence=ev.match_evidence,
            )
            for ev in p.evidence_records
        ]

        cat = p.category or "other"
        category_counts[cat] = category_counts.get(cat, 0) + 1

        profile_responses.append(
            ProfileResponse(
                id=p.id,
                platform=p.platform,
                category=p.category,
                username=p.username,
                profile_url=p.profile_url,
                display_name=p.display_name,
                biography=p.biography,
                public_website=p.public_website,
                profile_image_url=p.profile_image_url,
                location=p.location,
                confidence_existence=p.confidence_existence,
                confidence_data=p.confidence_data,
                identity_confidence=p.identity_confidence,
                first_seen_at=p.first_seen_at,
                last_checked_at=p.last_checked_at,
                evidence_records=evidence_list,
            )
        )

    audit_report = None
    if inv.options_json:
        try:
            import json
            opts = json.loads(inv.options_json)
            audit_report = opts.get("email_audit_report") or opts.get("phone_audit_report")
        except Exception:
            pass

    summary = {
        "target": inv.target_value,
        "search_type": inv.search_type,
        "status": inv.status,
        "total_sites_checked": inv.total_sites_checked,
        "verified_profiles_count": len(profile_responses),
        "inconclusive_count": inv.inconclusive_count,
        "category_breakdown": category_counts,
        "audit_report": audit_report,
    }

    return InvestigationResultsResponse(
        investigation=InvestigationSummary.model_validate(inv),
        profiles=profile_responses,
        verified_count=len(profile_responses),
        inconclusive_count=inv.inconclusive_count,
        summary=summary,
    )


@router.get("/{id}/graph")
async def get_investigation_graph(
    id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the evidence-correlated graph (nodes & edges) for React Flow visualization.
    """
    service = InvestigationService(db)
    inv = await service.repo.get_by_id(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    check_investigation_access(inv, current_user, require_modify=False)

    graph = await service.get_graph(id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph unavailable.")
    return graph.model_dump()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investigation(
    id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-deletes and purges an investigation. Enforces user ownership.
    """
    service = InvestigationService(db)
    inv = await service.repo.get_by_id(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    check_investigation_access(inv, current_user, require_modify=True)

    await service.repo.soft_delete(id)
    return None

