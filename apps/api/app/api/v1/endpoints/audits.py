"""
Email and Phone Self-Audit Endpoints
Enforces authorized self-audit workflows with OTP verification.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database.session import get_db
from apps.api.app.models import User, Profile, Evidence
from apps.api.app.core.security import get_optional_current_user
from apps.api.app.services.email_audit_service import EmailAuditService
from apps.api.app.services.phone_audit_service import PhoneAuditService
from apps.api.app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/audits", tags=["Self-Audits"])


class EmailChallengeRequest(BaseModel):
    email: EmailStr


class EmailVerifyRequest(BaseModel):
    challenge_id: str
    code: str


class PhoneChallengeRequest(BaseModel):
    phone: str


class PhoneVerifyRequest(BaseModel):
    challenge_id: str
    code: str


# --- Email Self-Audit ---

@router.post("/email/challenge")
async def request_email_challenge(payload: EmailChallengeRequest):
    """
    Dispatches a 6-digit verification code to the target email address.
    Required before performing an authorized email footprint audit.
    """
    res = EmailAuditService.request_otp(payload.email)
    return res


@router.post("/email/verify")
async def verify_email_and_audit(
    payload: EmailVerifyRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validates email verification OTP and performs authorized footprint audit.
    Stores the investigation in the user's history and returns the footprint report.
    """
    audit_token = EmailAuditService.verify_otp(payload.challenge_id, payload.code)
    if not audit_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    try:
        report = await EmailAuditService.audit_email(audit_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save to investigations table for persistence and history tracking
    service = InvestigationService(db)
    inv = await service.create_investigation(
        target_value=report["email"],
        search_type="email",
        user_id=current_user.id if current_user else None,
        options={"email_audit_report": report},
    )

    verified_count = 0

    # 1. Persist Curated Public Profiles (GitHub, GitLab, Instagram, YouTube, Snapchat, etc.)
    for cp in report.get("curated_profiles", []):
        verified_count += 1
        prof = Profile(
            investigation_id=inv.id,
            platform=cp["platform"],
            category=cp.get("category", "other"),
            username=cp["username"],
            profile_url=cp["profile_url"],
            display_name=cp.get("display_name"),
            biography=cp.get("biography"),
            public_website=cp.get("public_website"),
            profile_image_url=cp.get("profile_image_url"),
            location=cp.get("location"),
            confidence_existence=cp.get("confidence_existence", 0.95),
            confidence_data=cp.get("confidence_data", 0.90),
            identity_confidence=cp.get("identity_confidence", 0.85),
        )
        db.add(prof)
        await db.flush()

        ev_info = cp.get("evidence", {})
        ev = Evidence(
            profile_id=prof.id,
            source_url=ev_info.get("source_url") or cp["profile_url"],
            evidence_type=ev_info.get("evidence_type", "curated_profile"),
            detection_method=ev_info.get("detection_method", "composite"),
            verification_status="verified",
            confidence_score=ev_info.get("confidence_score", 0.95),
            observed_at=datetime.now(timezone.utc),
            match_evidence=ev_info.get("match_evidence") or "Public profile signature verified.",
        )
        db.add(ev)

    # 2. Persist Email Registered Services (Spotify, Replit, WordPress, CodePen, Office 365, Eventbrite, Duolingo, etc.)
    for es in report.get("email_services", []):
        verified_count += 1
        svc_name = es.get("name", "Service").capitalize()
        domain = es.get("domain", f"{es.get('name')}.com")
        svc_prof = Profile(
            investigation_id=inv.id,
            platform=svc_name,
            category="software",
            username=report["email"].split("@")[0],
            profile_url=f"https://{domain}",
            display_name=f"{svc_name} Account",
            biography=f"Active registered account associated with verified email {report['email']} (Method: {es.get('method', 'registration')})",
            confidence_existence=0.98,
            confidence_data=0.90,
            identity_confidence=0.95,
        )
        db.add(svc_prof)
        await db.flush()

        ev = Evidence(
            profile_id=svc_prof.id,
            source_url=f"https://{domain}",
            evidence_type="email_registration_confirmed",
            detection_method=es.get("method", "registration"),
            verification_status="verified",
            confidence_score=0.98,
            observed_at=datetime.now(timezone.utc),
            match_evidence=f"Confirmed active account on {domain} via authorized email registration audit.",
        )
        db.add(ev)

    # 3. If Gravatar profile exists, persist profile & evidence record
    gravatar_data = report.get("gravatar", {})
    if gravatar_data.get("exists"):
        verified_count += 1
        grav_profile = Profile(
            investigation_id=inv.id,
            platform="Gravatar",
            category="social",
            username=report["email"].split("@")[0],
            profile_url=gravatar_data.get("profile_url") or f"https://gravatar.com/{report['email_hash']}",
            display_name=gravatar_data.get("display_name") or report["email"].split("@")[0],
            biography=gravatar_data.get("about_me"),
            profile_image_url=gravatar_data.get("avatar_url"),
            confidence_existence=0.99,
            confidence_data=0.90,
            identity_confidence=0.95,
        )
        db.add(grav_profile)
        await db.flush()

        ev = Evidence(
            profile_id=grav_profile.id,
            source_url=grav_profile.profile_url,
            evidence_type="email_gravatar_match",
            detection_method="json_api",
            verification_status="verified",
            confidence_score=0.98,
            observed_at=datetime.now(timezone.utc),
            match_evidence=f"Verified public Gravatar profile for hash {report['email_hash']}",
        )
        db.add(ev)

    # Mark investigation as completed
    await service.repo.update_status(
        investigation_id=inv.id,
        status="completed",
        total_sites_checked=39 * 2 + len(report.get("email_services", [])) + 10,
        verified_count=verified_count,
        inconclusive_count=0,
        completed=True,
    )

    report["investigation_id"] = inv.id
    return report


# --- Phone Self-Audit ---

@router.post("/phone/challenge")
async def request_phone_challenge(payload: PhoneChallengeRequest):
    """
    Dispatches a 6-digit verification code to the target phone number.
    Enforces E.164 number format.
    """
    try:
        res = PhoneAuditService.request_otp(payload.phone)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/phone/verify")
async def verify_phone_and_audit(
    payload: PhoneVerifyRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validates phone verification OTP and performs authorized numbering plan & footprint audit.
    Stores the investigation in the user's history and returns the numbering report.
    """
    audit_token = PhoneAuditService.verify_otp(payload.challenge_id, payload.code)
    if not audit_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    try:
        report = PhoneAuditService.audit_phone(audit_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = InvestigationService(db)
    inv = await service.create_investigation(
        target_value=report["phone"],
        search_type="phone",
        user_id=current_user.id if current_user else None,
        options={"phone_audit_report": report},
    )

    # Persist verified telecom profile
    geo = report.get("geographic_metadata", {})
    phone_profile = Profile(
        investigation_id=inv.id,
        platform="Telecommunication Network",
        category="tech",
        username=report["phone"],
        profile_url=f"tel:{report['phone']}",
        display_name=f"{report['phone']} ({geo.get('country', 'Global')})",
        biography=f"Line Type: {geo.get('line_type', 'Mobile')} | Country ISO: {geo.get('iso_code', 'XX')}",
        confidence_existence=0.99,
        confidence_data=0.95,
        identity_confidence=0.99,
    )
    db.add(phone_profile)
    await db.flush()

    ev = Evidence(
        profile_id=phone_profile.id,
        source_url=phone_profile.profile_url,
        evidence_type="phone_e164_verification",
        detection_method="status_code",
        verification_status="verified",
        confidence_score=0.99,
        observed_at=datetime.now(timezone.utc),
        match_evidence=f"Authorized OTP verification confirmed ownership of {report['phone']}",
    )
    db.add(ev)

    await service.repo.update_status(
        investigation_id=inv.id,
        status="completed",
        total_sites_checked=1,
        verified_count=1,
        inconclusive_count=0,
        completed=True,
    )

    report["investigation_id"] = inv.id
    return report

