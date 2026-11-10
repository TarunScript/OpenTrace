"""
Profile Information Extraction and Normalization
Extracts publicly available profile attributes: display name, bio, avatar, website, location.
Calculates Profile Data Confidence.
"""
import re
import html
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from packages.schemas import SiteDefinition, ProfileData


class ProfileExtractor:
    """
    Extracts structured profile details from HTML or JSON responses.
    """

    @classmethod
    def clean_text(cls, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        # Unescape HTML entities & clean whitespace
        unescaped = html.unescape(text)
        cleaned = re.sub(r'\s+', ' ', unescaped).strip()
        # Remove any lingering HTML tags
        cleaned = re.sub(r'<[^>]+>', '', cleaned).strip()
        return cleaned if cleaned else None

    @classmethod
    def clean_url(cls, raw_url: Optional[str], base_url: str) -> Optional[str]:
        if not raw_url:
            return None
        cleaned = raw_url.strip()
        if cleaned.startswith("//"):
            cleaned = "https:" + cleaned
        elif cleaned.startswith("/"):
            cleaned = urljoin(base_url, cleaned)
        elif not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            cleaned = "https://" + cleaned

        # Validate URL structure
        try:
            parsed = urlparse(cleaned)
            if parsed.netloc and parsed.scheme in ("http", "https"):
                return cleaned
        except Exception:
            pass
        return None

    @classmethod
    def extract(
        cls,
        site: SiteDefinition,
        target_username: str,
        profile_url: str,
        body_text: str,
        confidence_existence: float,
    ) -> Tuple[ProfileData, float]:
        """
        Extracts metadata using site regex rules and standard HTML meta tags.
        Returns:
            (ProfileData, confidence_data)
        """
        display_name: Optional[str] = None
        bio: Optional[str] = None
        avatar_url: Optional[str] = None
        website: Optional[str] = None
        location: Optional[str] = None

        # 1. Apply site-specific regex extraction rules if defined
        if site.extract_display_name_regex:
            m = re.search(site.extract_display_name_regex, body_text, re.IGNORECASE | re.DOTALL)
            if m and m.group(1):
                display_name = cls.clean_text(m.group(1))

        if site.extract_bio_regex:
            m = re.search(site.extract_bio_regex, body_text, re.IGNORECASE | re.DOTALL)
            if m and m.group(1):
                bio = cls.clean_text(m.group(1))

        if site.extract_avatar_regex:
            m = re.search(site.extract_avatar_regex, body_text, re.IGNORECASE | re.DOTALL)
            if m and m.group(1):
                avatar_url = cls.clean_url(m.group(1), profile_url)

        if site.extract_website_regex:
            m = re.search(site.extract_website_regex, body_text, re.IGNORECASE | re.DOTALL)
            if m and m.group(1):
                website = cls.clean_url(m.group(1), profile_url)

        # 2. Fallback to standard OpenGraph & Meta tags if not extracted
        try:
            soup = BeautifulSoup(body_text[:50000], "html.parser")

            if not display_name:
                og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
                if og_title and og_title.get("content"):
                    raw = og_title.get("content")
                    # Clean title: e.g. "Tarun Kumar (@tarun_dev) on X" -> extract name
                    display_name = cls.clean_text(raw)
                elif soup.title and soup.title.string:
                    display_name = cls.clean_text(soup.title.string)

            if not bio:
                og_desc = (
                    soup.find("meta", property="og:description")
                    or soup.find("meta", attrs={"name": "twitter:description"})
                    or soup.find("meta", attrs={"name": "description"})
                )
                if og_desc and og_desc.get("content"):
                    bio = cls.clean_text(og_desc.get("content"))

            if not avatar_url:
                og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if og_image and og_image.get("content"):
                    avatar_url = cls.clean_url(og_image.get("content"), profile_url)

            # Location extraction heuristic from vcard or itemprop
            loc_tag = soup.find(attrs={"itemprop": "homeLocation"}) or soup.find(class_=re.compile(r"location", re.I))
            if loc_tag:
                location = cls.clean_text(loc_tag.get_text())

        except Exception:
            # HTML parsing failed; regex results stand
            pass

        # 3. Calculate Profile Data Confidence
        # How reliable is the extracted profile data?
        score = 0.20  # Base
        if display_name and display_name.lower() != target_username.lower():
            score += 0.25
        if bio and len(bio) > 10:
            score += 0.25
        if avatar_url:
            score += 0.15
        if website:
            score += 0.15

        confidence_data = min(round(score, 2), 0.95)

        profile = ProfileData(
            platform=site.name,
            username=target_username,
            profile_url=profile_url,
            category=site.category,
            display_name=display_name,
            biography=bio,
            public_website=website,
            profile_image_url=avatar_url,
            location=location,
            confidence_existence=confidence_existence,
            confidence_data=confidence_data,
            identity_confidence=0.50, # Initial prior for exact username match
        )
        return profile, confidence_data

