import pytest
from packages.schemas import (
    SiteDefinition,
    PlatformCategory,
    VerificationStatus,
    DetectionMethod,
)
from packages.osint_engine.detectors.classifier import ResponseClassifier

test_site = SiteDefinition(
    name="TestPlatform",
    category=PlatformCategory.DEVELOPER,
    url_pattern="https://example.com/user/{username}",
    check_type=DetectionMethod.COMPOSITE,
    expected_status=[200],
    not_found_status=[404],
    absence_indicators=["User not found", "This profile has been deleted"],
    presence_indicators=['class="user-profile"', 'data-user="{username}"'],
)


def test_classify_explicit_404():
    status, conf, evidence = ResponseClassifier.classify(
        site=test_site,
        status_code=404,
        final_url="https://example.com/user/ghost",
        body_text="<html><body>404 Not Found</body></html>",
        headers={},
        latency_ms=120.0,
        target_username="ghost",
    )
    assert status == VerificationStatus.NOT_FOUND
    assert conf == 0.0
    assert evidence.status_code == 404


def test_classify_soft_404_on_200():
    # Site returns 200 OK, but body says "User not found"
    status, conf, evidence = ResponseClassifier.classify(
        site=test_site,
        status_code=200,
        final_url="https://example.com/user/ghost",
        body_text="<html><body><h1>User not found</h1><p>Sorry!</p></body></html>",
        headers={},
        latency_ms=150.0,
        target_username="ghost",
    )
    assert status == VerificationStatus.NOT_FOUND
    assert "soft_404" in evidence.evidence_type


def test_classify_rate_limit_429():
    status, conf, evidence = ResponseClassifier.classify(
        site=test_site,
        status_code=429,
        final_url="https://example.com/user/busy",
        body_text="Too Many Requests",
        headers={},
        latency_ms=80.0,
        target_username="busy",
    )
    assert status == VerificationStatus.INCONCLUSIVE
    assert evidence.evidence_type == "rate_limit"


def test_classify_captcha_challenge():
    status, conf, evidence = ResponseClassifier.classify(
        site=test_site,
        status_code=200,
        final_url="https://example.com/user/test",
        body_text="<html><script src='https://challenges.cloudflare.com/turnstile/v0/api.js'></script></html>",
        headers={},
        latency_ms=90.0,
        target_username="test",
    )
    assert status == VerificationStatus.INCONCLUSIVE
    assert evidence.evidence_type == "anti_bot_challenge"


def test_classify_genuine_profile():
    body = (
        '<html><div class="user-profile">'
        '<span data-user="realdev">realdev</span>'
        '<h1>Real Developer</h1>'
        '</div></html>'
    )
    status, conf, evidence = ResponseClassifier.classify(
        site=test_site,
        status_code=200,
        final_url="https://example.com/user/realdev",
        body_text=body,
        headers={},
        latency_ms=110.0,
        target_username="realdev",
    )
    assert status == VerificationStatus.VERIFIED
    assert conf >= 0.70
    assert evidence.verification_status == VerificationStatus.VERIFIED

