"""
Pydantic API Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from packages.schemas import PlatformCategory, VerificationStatus


# Authentication Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    is_verified: bool
    created_at: datetime


# Investigation Schemas
class InvestigationOptions(BaseModel):
    deep_search: bool = False
    max_depth: int = 1
    categories: Optional[List[PlatformCategory]] = None


class InvestigationCreate(BaseModel):
    type: str = "username" # "username", "email", "phone"
    value: str = Field(..., min_length=1, max_length=100)
    options: Optional[InvestigationOptions] = Field(default_factory=InvestigationOptions)


class InvestigationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    search_type: str
    target_value: str
    status: str
    total_sites_checked: int = 0
    verified_count: int = 0
    inconclusive_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_url: str
    evidence_type: str
    detection_method: str
    verification_status: str
    confidence_score: float
    observed_at: datetime
    match_evidence: Optional[str] = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str
    category: str
    username: str
    profile_url: str
    display_name: Optional[str] = None
    biography: Optional[str] = None
    public_website: Optional[str] = None
    profile_image_url: Optional[str] = None
    location: Optional[str] = None
    confidence_existence: float
    confidence_data: float
    identity_confidence: float
    first_seen_at: datetime
    last_checked_at: datetime
    evidence_records: List[EvidenceResponse] = []


class InvestigationResultsResponse(BaseModel):
    investigation: InvestigationSummary
    profiles: List[ProfileResponse]
    verified_count: int
    inconclusive_count: int
    summary: Dict[str, Any]


class SiteResponse(BaseModel):
    name: str
    category: str
    url_pattern: str
    check_type: str
    is_active: bool
