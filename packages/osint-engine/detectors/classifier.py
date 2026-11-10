"""
Response Classification and Confidence Evaluation Engine
Crucial Principle: HTTP 200 alone NEVER proves profile existence.
Distinguishes genuine profiles, soft 404s, login walls, CAPTCHAs, rate limits, and redirects.
"""
import re
from typing import Tuple, Dict, Any, Optional
from packages.schemas import (
    SiteDefinition,
    VerificationStatus,
    DetectionMethod,
    EvidenceModel,
)


class ResponseClassifier:
    """
    Classifies raw HTTP responses into definitive verification states with confidence scoring.
    """

    GENERIC_LOGIN_INDICATORS = [
        "sign in to your account",
        "log in to continue",
        "please sign in",
        "login to view this profile",
        "create an account or log in",
    ]

    GENERIC_SOFT_404_INDICATORS = [
        "page not found",
        "this page doesn't exist",
        "user not found",
        "user does not exist",
        "profile not found",
        "account suspended",
        "this profile is no longer available",
        "the link you followed may be broken",
        "404 not found",
        "we can't find that page",
    ]

    CAPTCHA_INDICATORS = [
        "cf-chl-bypass",
        "challenge-running",
        "cf-browser-verification",
        "client challenge",
        "cloudflare ray id",
        "recaptcha",
        "hcaptcha",
        "ddos-guard",
        "perimeterx",
        "security check to continue",
        "are you a human",
    ]

    @classmethod
    def classify(
        cls,
        site: SiteDefinition,
        status_code: int,
        final_url: str,
        body_text: str,
        headers: Dict[str, str],
        latency_ms: float,
        target_username: str,
    ) -> Tuple[VerificationStatus, float, EvidenceModel]:
        """
        Evaluates HTTP response against multi-layer heuristics.
        Returns:
            (VerificationStatus, existence_confidence_score, EvidenceModel)
        """
        body_lower = body_text.lower()
        evidence_details: Dict[str, Any] = {
            "status_code": status_code,
            "final_url": final_url,
            "latency_ms": latency_ms,
        }

        # 1. Rate Limiting Check
        if status_code == 429 or "too many requests" in body_lower or "rate limit" in body_lower:
            evidence = EvidenceModel(
                source_url=final_url,
                evidence_type="rate_limit",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.INCONCLUSIVE,
                confidence_score=0.0,
                status_code=status_code,
                response_time_ms=latency_ms,
                match_evidence="Target service returned HTTP 429 / Rate Limit indicator.",
                raw_details=evidence_details,
            )
            return VerificationStatus.INCONCLUSIVE, 0.0, evidence

        # 2. CAPTCHA / Anti-Bot Challenge Check
        for captcha_token in cls.CAPTCHA_INDICATORS + site.captcha_indicators:
            if captcha_token.lower() in body_lower:
                evidence = EvidenceModel(
                    source_url=final_url,
                    evidence_type="anti_bot_challenge",
                    detection_method=DetectionMethod.COMPOSITE,
                    verification_status=VerificationStatus.INCONCLUSIVE,
                    confidence_score=0.0,
                    status_code=status_code,
                    response_time_ms=latency_ms,
                    match_evidence=f"Anti-bot or CAPTCHA challenge detected: '{captcha_token}'",
                    raw_details=evidence_details,
                )
                return VerificationStatus.INCONCLUSIVE, 0.0, evidence

        # 3. Explicit HTTP 404 / Known Not Found Status Codes
        if status_code in site.not_found_status and status_code not in site.expected_status:
            evidence = EvidenceModel(
                source_url=final_url,
                evidence_type="http_not_found",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.NOT_FOUND,
                confidence_score=1.0,
                status_code=status_code,
                response_time_ms=latency_ms,
                match_evidence=f"Status code {status_code} matched expected not_found_status.",
                raw_details=evidence_details,
            )
            return VerificationStatus.NOT_FOUND, 0.0, evidence

        # 4. Redirect to login page or generic home page
        parsed_path = final_url.split("?")[0].rstrip("/")
        if any(login_kw in parsed_path for login_kw in ["/login", "/signin", "/auth"]):
            evidence = EvidenceModel(
                source_url=final_url,
                evidence_type="redirect_to_login",
                detection_method=DetectionMethod.HEADER_REDIRECT,
                verification_status=VerificationStatus.INCONCLUSIVE,
                confidence_score=0.0,
                status_code=status_code,
                response_time_ms=latency_ms,
                match_evidence=f"Redirected to authentication gate: {final_url}",
                raw_details=evidence_details,
            )
            return VerificationStatus.INCONCLUSIVE, 0.0, evidence

        # 5. Absence Indicators (Soft 404 Detection)
        # Check site-specific absence indicators
        for token in site.absence_indicators:
            formatted_token = token.replace("{username}", target_username).lower()
            if formatted_token in body_lower:
                evidence = EvidenceModel(
                    source_url=final_url,
                    evidence_type="soft_404_site_indicator",
                    detection_method=DetectionMethod.BODY_CONTAINS,
                    verification_status=VerificationStatus.NOT_FOUND,
                    confidence_score=0.95,
                    status_code=status_code,
                    response_time_ms=latency_ms,
                    match_evidence=f"Detected soft-404 string in response: '{token}'",
                    raw_details=evidence_details,
                )
                return VerificationStatus.NOT_FOUND, 0.0, evidence

        # Check generic soft-404 indicators if status code is 200
        if status_code == 200:
            for generic_token in cls.GENERIC_SOFT_404_INDICATORS:
                if generic_token in body_lower:
                    # Look closer: if the token is in title or prominent heading
                    if f"<title>{generic_token}" in body_lower or f"<h1>{generic_token}" in body_lower or len(body_text) < 1500:
                        evidence = EvidenceModel(
                            source_url=final_url,
                            evidence_type="soft_404_heuristic",
                            detection_method=DetectionMethod.SOFT_404_HEURISTIC,
                            verification_status=VerificationStatus.NOT_FOUND,
                            confidence_score=0.85,
                            status_code=status_code,
                            response_time_ms=latency_ms,
                            match_evidence=f"Generic soft-404 indicator matched: '{generic_token}'",
                            raw_details=evidence_details,
                        )
                        return VerificationStatus.NOT_FOUND, 0.0, evidence

        # 6. Presence Indicators (Positive Evidence)
        presence_matched = []
        for p_token in site.presence_indicators:
            formatted_p_token = p_token.replace("{username}", target_username)
            if formatted_p_token.lower() in body_lower:
                presence_matched.append(p_token)

        # 7. Final Verification Decision
        if status_code in site.expected_status:
            # If site defines explicit presence indicators
            if site.presence_indicators:
                if presence_matched:
                    # Verified with high existence confidence
                    confidence = min(0.70 + (0.15 * len(presence_matched)), 0.99)
                    evidence = EvidenceModel(
                        source_url=final_url,
                        evidence_type="positive_profile_signature",
                        detection_method=site.check_type,
                        verification_status=VerificationStatus.VERIFIED,
                        confidence_score=round(confidence, 2),
                        status_code=status_code,
                        response_time_ms=latency_ms,
                        match_evidence=f"HTTP {status_code} and verified {len(presence_matched)} positive indicators.",
                        raw_details={"matched_indicators": presence_matched, **evidence_details},
                    )
                    return VerificationStatus.VERIFIED, round(confidence, 2), evidence
                else:
                    # Status code was expected, but required presence indicators were missing!
                    # Strictly INCONCLUSIVE (never falsely verified)
                    evidence = EvidenceModel(
                        source_url=final_url,
                        evidence_type="missing_profile_structure",
                        detection_method=DetectionMethod.COMPOSITE,
                        verification_status=VerificationStatus.INCONCLUSIVE,
                        confidence_score=0.20,
                        status_code=status_code,
                        response_time_ms=latency_ms,
                        match_evidence=f"HTTP {status_code} received, but specific profile markers were not found.",
                        raw_details=evidence_details,
                    )
                    return VerificationStatus.INCONCLUSIVE, 0.20, evidence

            # If site relies purely on JSON API
            if site.check_type == DetectionMethod.JSON_API:
                confidence = 0.90
                evidence = EvidenceModel(
                    source_url=final_url,
                    evidence_type="json_api_response",
                    detection_method=DetectionMethod.JSON_API,
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=confidence,
                    status_code=status_code,
                    response_time_ms=latency_ms,
                    match_evidence="Valid JSON user object returned by public API.",
                    raw_details=evidence_details,
                )
                return VerificationStatus.VERIFIED, confidence, evidence

            # Standard 200 without positive indicators: strictly INCONCLUSIVE
            # (HTTP 200 alone NEVER proves profile existence)
            confidence = 0.30
            evidence = EvidenceModel(
                source_url=final_url,
                evidence_type="http_status_ok_inconclusive",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.INCONCLUSIVE,
                confidence_score=confidence,
                status_code=status_code,
                response_time_ms=latency_ms,
                match_evidence=f"HTTP {status_code} received without negative indicators, but lacked unique presence proof.",
                raw_details=evidence_details,
            )
            return VerificationStatus.INCONCLUSIVE, confidence, evidence

        # Any other status code
        evidence = EvidenceModel(
            source_url=final_url,
            evidence_type="unexpected_status",
            detection_method=DetectionMethod.STATUS_CODE,
            verification_status=VerificationStatus.INCONCLUSIVE,
            confidence_score=0.1,
            status_code=status_code,
            response_time_ms=latency_ms,
            match_evidence=f"Unexpected status code: {status_code}",
            raw_details=evidence_details,
        )
        return VerificationStatus.INCONCLUSIVE, 0.1, evidence

