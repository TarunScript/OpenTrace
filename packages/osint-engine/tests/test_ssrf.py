import pytest
import httpx
from packages.osint_engine.core.ssrf import (
    validate_target_url,
    parse_and_validate_ip,
    is_ip_blocked,
    SSRFProtectedNetworkBackend,
)
from packages.osint_engine.core.exceptions import SSRFViolationError
from packages.osint_engine.adapters.curated_adapter import CuratedOSINTAdapter
from packages.schemas import SiteDefinition, PlatformCategory, VerificationStatus, DetectionMethod


def test_ssrf_blocks_private_ips():
    dangerous_urls = [
        "http://127.0.0.1/admin",
        "http://127.0.0.1:80/metrics",
        "http://localhost/secret",
        "http://10.0.0.5/internal",
        "http://192.168.1.1/router",
        "http://172.16.0.2/api",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]
    for url in dangerous_urls:
        with pytest.raises(SSRFViolationError):
            validate_target_url(url)


def test_ssrf_blocks_unusual_ip_encodings():
    unusual_urls = [
        "http://2130706433/",                # Decimal representation of 127.0.0.1
        "http://0x7f000001/",                # Hex representation of 127.0.0.1
        "http://0177.0.0.1/",                # Dotted octal of 127.0.0.1
        "http://017700000001/",              # Single octal number of 127.0.0.1
        "http://127.1/",                     # Shortened classful of 127.0.0.1
        "http://[::1]/",                     # IPv6 loopback
        "http://[::ffff:127.0.0.1]/",        # IPv4-mapped IPv6 loopback
        "http://[::ffff:169.254.169.254]/",  # IPv4-mapped IPv6 cloud metadata
        "http://[fe80::1%eth0]/",            # IPv6 link-local with scope ID
        "http://127.0.0.1./",                # Dotted quad with trailing dot
    ]
    for url in unusual_urls:
        with pytest.raises(SSRFViolationError):
            validate_target_url(url)


def test_ssrf_blocks_credentials_and_ports():
    invalid_urls = [
        "http://admin:secret@github.com/",
        "http://attacker.com@127.0.0.1/",
        "http://github.com:22/",             # SSH port
        "http://github.com:6379/",           # Redis port
        "http://github.com:5432/",           # Postgres port
        "http://github.com:3306/",           # MySQL port
        "http://github.com\x00/",            # Null byte injection
    ]
    for url in invalid_urls:
        with pytest.raises(SSRFViolationError):
            validate_target_url(url)


def test_ssrf_blocks_non_http():
    with pytest.raises(SSRFViolationError):
        validate_target_url("file:///etc/passwd")
    with pytest.raises(SSRFViolationError):
        validate_target_url("gopher://127.0.0.1:70")
    with pytest.raises(SSRFViolationError):
        validate_target_url("ftp://127.0.0.1/")


def test_ssrf_allows_legitimate_domains():
    safe_urls = [
        "https://github.com/torvalds",
        "https://reddit.com/user/test",
        "https://news.ycombinator.com/user?id=dang",
        "https://mastodon.social/@example",
    ]
    for url in safe_urls:
        validate_target_url(url)


@pytest.mark.asyncio
async def test_ssrf_blocks_redirect_to_private_ip():
    site = SiteDefinition(
        name="RedirectTestSite",
        category=PlatformCategory.DEVELOPER,
        url_pattern="https://example.com/user/{username}",
        check_type=DetectionMethod.STATUS_CODE,
    )

    def redirect_handler(request: httpx.Request):
        return httpx.Response(302, headers={"Location": "http://127.0.0.1:80/internal"})

    transport = httpx.MockTransport(redirect_handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        adapter = CuratedOSINTAdapter(sites=[site])
        result = await adapter.check_site(site, "attacker", client=mock_client)
        assert result.status == VerificationStatus.ERROR
        assert "SSRF" in (result.error_message or "")


@pytest.mark.asyncio
async def test_ssrf_protected_network_backend_blocks_private():
    backend = SSRFProtectedNetworkBackend()
    # Connecting directly to a private IP literal must raise SSRFViolationError
    with pytest.raises(SSRFViolationError):
        await backend.connect_tcp("127.0.0.1", 80)
    with pytest.raises(SSRFViolationError):
        await backend.connect_tcp("169.254.169.254", 80)
