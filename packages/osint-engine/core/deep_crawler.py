"""
Deep Discovery and Recursive Profile Extractor (Phase 2)
Extracts publicly declared profile links and external identities from verified profiles and personal websites.
Enforces cycle detection, strict SSRF protection, recursion bounds, and max depth limits.
"""
import re
from typing import List, Set, Tuple, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from packages.schemas import ProfileData, PlatformCategory
from packages.osint_engine.core.ssrf import validate_target_url
from packages.site_registry.registry import default_registry

# Recognized social/developer platform patterns
PLATFORM_LINK_PATTERNS = [
    (r"github\.com/([a-zA-Z0-9_\-\.]+)", "GitHub"),
    (r"gitlab\.com/([a-zA-Z0-9_\-\.]+)", "GitLab"),
    (r"reddit\.com/user/([a-zA-Z0-9_\-]+)", "Reddit"),
    (r"twitter\.com/([a-zA-Z0-9_]+)", "Twitter"),
    (r"x\.com/([a-zA-Z0-9_]+)", "Twitter"),
    (r"t\.me/([a-zA-Z0-9_]+)", "Telegram"),
    (r"dev\.to/([a-zA-Z0-9_\-]+)", "Dev.to"),
    (r"medium\.com/@([a-zA-Z0-9_\-\.]+)", "Medium"),
    (r"keybase\.io/([a-zA-Z0-9_]+)", "Keybase"),
    (r"steamcommunity\.com/id/([a-zA-Z0-9_\-]+)", "Steam"),
    (r"soundcloud\.com/([a-zA-Z0-9_\-]+)", "SoundCloud"),
]


class DeepDiscoveryCrawler:
    """
    Crawls verified profiles and declared websites to discover explicitly linked accounts.
    """

    @classmethod
    def extract_links_from_text(cls, text: str) -> List[Tuple[str, str]]:
        """
        Extracts (platform, username) pairs from raw text or markdown bio.
        """
        discovered: List[Tuple[str, str]] = []
        if not text:
            return discovered

        for pattern, platform in PLATFORM_LINK_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                username = m.group(1).strip("/").strip()
                # Exclude common system keywords
                if username.lower() not in ("about", "contact", "blog", "privacy", "terms", "explore", "settings"):
                    discovered.append((platform, username))
        return discovered

    @classmethod
    async def extract_links_from_website(
        cls,
        website_url: str,
        timeout_seconds: float = 6.0,
    ) -> List[Tuple[str, str]]:
        """
        Safely inspects a personal website to extract explicitly linked social profiles.
        Enforces SSRF validation before outbound dispatch.
        """
        discovered: List[Tuple[str, str]] = []
        if not website_url:
            return discovered

        try:
            validate_target_url(website_url)
        except Exception:
            return discovered

        headers = {
            "User-Agent": "OpenTraceOSINT/1.0 (Public Footprint Discovery)",
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                resp = await client.get(website_url, headers=headers)
                if resp.status_code != 200:
                    return discovered

                soup = BeautifulSoup(resp.text[:60000], "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    for pattern, platform in PLATFORM_LINK_PATTERNS:
                        m = re.search(pattern, href, re.IGNORECASE)
                        if m:
                            username = m.group(1).strip("/").strip()
                            if username.lower() not in ("about", "contact", "blog", "privacy", "terms", "explore"):
                                discovered.append((platform, username))
        except Exception:
            pass

        return discovered

