"""
B2C & Consumer Platform Prober Adapter
Performs strictly verified, live public API checks without synthetic or fabricated data:
- Duolingo Public User Directory API
"""
import asyncio
from typing import List, Dict, Any, Optional
import httpx

from packages.schemas import PlatformCategory


class B2CAdapter:
    """
    Coordinates asynchronous probing of verified public endpoints.
    Strictly reports only accounts that return confirmed positive HTTP responses.
    Never synthesizes or fabricates phone numbers or account existence.
    """

    @classmethod
    async def probe_duolingo(cls, email: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """
        Queries Duolingo's public user endpoint.
        Returns profile details only if a genuine account exists for this email.
        """
        try:
            r = await client.get(
                f"https://www.duolingo.com/2017-06-30/users?email={email.strip().lower()}",
                headers={"User-Agent": "OpenTrace/1.0 (OSINT Digital Footprint Engine)"}
            )
            if r.status_code == 200:
                users = r.json().get("users", [])
                if users:
                    u = users[0]
                    username = u.get("username")
                    fullname = u.get("name")
                    avatar = u.get("picture")
                    streak = u.get("streak", 0)
                    return {
                        "name": "duolingo",
                        "display_name": "Duolingo",
                        "domain": "duolingo.com",
                        "category": PlatformCategory.FORUMS.value,
                        "exists": True,
                        "method": "public_api",
                        "username": username,
                        "fullname": fullname or username,
                        "avatar": avatar,
                        "phoneNumber": None,
                        "emailrecovery": None,
                        "profile_url": f"https://www.duolingo.com/profile/{username}" if username else "https://www.duolingo.com",
                        "evidence_text": f"Active Duolingo learner (Username: {username}, Streak: {streak})",
                    }
        except Exception:
            pass
        return None

    @classmethod
    async def scan_all_b2c(cls, email: str) -> List[Dict[str, Any]]:
        """
        Concurrently probes verified live public endpoints for a given email address.
        Only returns verified live discoveries.
        """
        clean_email = email.strip().lower()
        results: List[Dict[str, Any]] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }

        async with httpx.AsyncClient(timeout=6.0, headers=headers, follow_redirects=True) as client:
            duo_res = await cls.probe_duolingo(clean_email, client)
            if duo_res and duo_res.get("exists"):
                results.append(duo_res)

        return results
