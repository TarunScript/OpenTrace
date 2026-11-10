"""
Email and Phone Self-Audit Endpoints
Enforces authorized self-audit workflows with OTP verification.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database.session import get_db
from apps.api.app.models import User
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

    report["investigation_id"] = inv.id
    return report
