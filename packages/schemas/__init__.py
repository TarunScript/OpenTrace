"""
OpenTrace Schemas Package
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def datetime_now_utc() -> datetime:
    return datetime.now(timezone.utc)


class PlatformCategory(str, Enum):
    SOCIAL = "social"
    DEVELOPER = "developer"
    FORUMS = "forums"
    GAMING = "gaming"
    MEDIA = "media"
    TECH = "tech"
    SHOPPING = "shopping"
    PRODUCTIVITY = "productivity"
    MESSAGING = "messaging"
    BLOGGING = "blogging"
    OTHER = "other"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"          # Explicit positive detection with high confidence
    UNVERIFIED = "unverified"      # Positive response with minor ambiguity
    INCONCLUSIVE = "inconclusive"  # Rate limited, captcha, timeout, anti-bot
    NOT_FOUND = "not_found"        # Confirmed 404 / negative detection
    ERROR = "error"                # Unhandled connection error


class DetectionMethod(str, Enum):
    STATUS_CODE = "status_code"
    BODY_CONTAINS = "body_contains"
    BODY_ABSENT = "body_absent"
    HEADER_REDIRECT = "header_redirect"
    JSON_API = "json_api"
    SOFT_404_HEURISTIC = "soft_404_heuristic"
    COMPOSITE = "composite"


class SearchType(str, Enum):
    USERNAME = "username"
    EMAIL = "email"
    PHONE = "phone"


class InvestigationStatus(str, Enum):
    QUEUED = "queued"
    SEARCHING = "searching"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvidenceModel(BaseModel):
    source_url: str
    evidence_type: str = "profile_probe"
    detection_method: DetectionMethod
    verification_status: VerificationStatus
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    adapter_version: str = "1.0.0"
    observed_at: datetime = Field(default_factory=datetime_now_utc)
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    match_evidence: Optional[str] = None
    raw_details: Optional[Dict[str, Any]] = None


class ProfileData(BaseModel):
    platform: str
    username: str
    profile_url: str
    category: PlatformCategory = PlatformCategory.OTHER
    display_name: Optional[str] = None
    biography: Optional[str] = None
    public_website: Optional[str] = None
    profile_image_url: Optional[str] = None
    location: Optional[str] = None
    first_seen_at: datetime = Field(default_factory=datetime_now_utc)
    last_checked_at: datetime = Field(default_factory=datetime_now_utc)
    
    # 3 Independent confidence dimensions
    confidence_existence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_data: float = Field(default=0.0, ge=0.0, le=1.0)
    identity_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    site_name: str
    category: PlatformCategory
    target_username: str
    status: VerificationStatus
    profile: Optional[ProfileData] = None
    evidence: Optional[EvidenceModel] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0


class SiteDefinition(BaseModel):
    name: str
    category: PlatformCategory
    url_pattern: str                    # e.g. "https://github.com/{username}"
    check_type: DetectionMethod = DetectionMethod.STATUS_CODE
    probe_url: Optional[str] = None     # Optional probe URL if different from profile
    http_method: str = "GET"            # HTTP method ("GET" or "POST")
    post_json: Optional[Dict[str, Any]] = None # Optional JSON payload for GraphQL/API probes
    expected_status: List[int] = [200]
    not_found_status: List[int] = [404]
    presence_indicators: List[str] = [] # Strings that MUST be present in page body
    absence_indicators: List[str] = []  # Strings that if present mean NOT found (soft 404)
    captcha_indicators: List[str] = [
        "cf-chl-bypass", "challenge-running", "g-recaptcha", "/recaptcha/api.js",
        "human verification", "ddos protection", "robot check"
    ]
    extract_display_name_regex: Optional[str] = None
    extract_bio_regex: Optional[str] = None
    extract_avatar_regex: Optional[str] = None
    extract_website_regex: Optional[str] = None
    custom_headers: Dict[str, str] = {}
    is_active: bool = True
    rate_limit_per_minute: int = 60

