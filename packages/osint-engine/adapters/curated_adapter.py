"""
Curated OSINT Search Adapter
High-performance asynchronous username footprint search adapter.
Enforces SSRF protection, multi-signal response classification, and real-time streaming.
"""
import asyncio
import time
from typing import AsyncIterator, List, Optional, Dict
import httpx

from packages.schemas import (
    SearchResult,
    SiteDefinition,
    PlatformCategory,
    VerificationStatus,
    EvidenceModel,
    DetectionMethod,
)
from packages.site_registry.registry import default_registry
from packages.osint_engine.adapters.base import BaseOSINTAdapter
from packages.osint_engine.core.ssrf import validate_target_url, SSRFProtectedTransport
from packages.osint_engine.core.exceptions import SSRFViolationError
from packages.osint_engine.detectors.classifier import ResponseClassifier
from packages.osint_engine.normalizers.extractor import ProfileExtractor

MAX_RESPONSE_BYTES = 1024 * 1024  # 1 MB maximum response size to prevent memory exhaustion / bombs

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class CuratedOSINTAdapter(BaseOSINTAdapter):
    """
    Standard OSINT adapter powered by the OpenTrace curated site registry.
    """

    def __init__(self, sites: Optional[List[SiteDefinition]] = None):
        super().__init__(name="OpenTrace Curated Engine", version="1.0.0")
        self._sites = sites if sites is not None else default_registry.list_all()

    def supported_sites(self) -> List[SiteDefinition]:
        return [s for s in self._sites if s.is_active]

    async def check_site(
        self,
        site: SiteDefinition,
        username: str,
        client: Optional[httpx.AsyncClient] = None,
        timeout_seconds: float = 8.0,
    ) -> SearchResult:
        """
        Executes an evidence-backed probe on a single site.
        """
        start_time = time.perf_counter()
        target_url = site.url_pattern.format(username=username)
        probe_url = site.probe_url.format(username=username) if site.probe_url else target_url

        # 1. SSRF Check
        try:
            validate_target_url(probe_url)
        except Exception as ssrf_err:
            latency_ms = (time.perf_counter() - start_time) * 1000
            evidence = EvidenceModel(
                source_url=probe_url,
                evidence_type="ssrf_blocked",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.ERROR,
                confidence_score=0.0,
                response_time_ms=latency_ms,
                match_evidence=f"SSRF Protection prevented request: {ssrf_err}",
            )
            return SearchResult(
                site_name=site.name,
                category=site.category,
                target_username=username,
                status=VerificationStatus.ERROR,
                evidence=evidence,
                error_message=str(ssrf_err),
                latency_ms=latency_ms,
            )

        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if site.custom_headers:
            headers.update(site.custom_headers)

        timeout_config = httpx.Timeout(
            timeout_seconds,
            connect=min(3.0, timeout_seconds),
            read=min(5.0, timeout_seconds),
            write=3.0,
            pool=5.0,
        )

        close_client = False
        if client is None:
            client = httpx.AsyncClient(
                transport=SSRFProtectedTransport(),
                timeout=timeout_config,
                follow_redirects=False,
            )
            close_client = True

        try:
            # Safe redirect following with SSRF validation on EVERY hop
            current_url = probe_url
            redirect_count = 0
            max_redirects = 5
            resp = None
            body_text = ""

            while True:
                validate_target_url(current_url)
                if site.http_method == "POST":
                    payload = {}
                    if site.post_json:
                        for k, v in site.post_json.items():
                            payload[k] = v.format(username=username) if isinstance(v, str) else v
                    req = client.build_request("POST", current_url, headers=headers, json=payload)
                else:
                    req = client.build_request("GET", current_url, headers=headers)

                resp = await client.send(req, stream=True)
                try:
                    # Check Content-Length header or stream bounded bytes
                    chunks = []
                    total_bytes = 0
                    async for chunk in resp.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > MAX_RESPONSE_BYTES:
                            remaining = MAX_RESPONSE_BYTES - (total_bytes - len(chunk))
                            if remaining > 0:
                                chunks.append(chunk[:remaining])
                            break
                        chunks.append(chunk)

                    raw_bytes = b"".join(chunks)
                    encoding = resp.encoding or "utf-8"
                    body_text = raw_bytes.decode(encoding, errors="replace")
                finally:
                    await resp.aclose()

                if resp.is_redirect and "location" in resp.headers and redirect_count < max_redirects:
                    redirect_count += 1
                    current_url = str(resp.url.join(resp.headers["location"]))
                    validate_target_url(current_url)
                    continue
                break

            latency_ms = (time.perf_counter() - start_time) * 1000

            # 2. Response Classification (HTTP 200 alone is NEVER proof)
            status, conf_exist, evidence = ResponseClassifier.classify(
                site=site,
                status_code=resp.status_code,
                final_url=str(resp.url),
                body_text=body_text,
                headers=dict(resp.headers),
                latency_ms=latency_ms,
                target_username=username,
            )

            # 3. Profile Information Extraction (strictly when verified)
            profile = None
            if status == VerificationStatus.VERIFIED:
                profile, conf_data = ProfileExtractor.extract(
                    site=site,
                    target_username=username,
                    profile_url=target_url,
                    body_text=body_text,
                    confidence_existence=conf_exist,
                )

            return SearchResult(
                site_name=site.name,
                category=site.category,
                target_username=username,
                status=status,
                profile=profile,
                evidence=evidence,
                latency_ms=latency_ms,
            )

        except SSRFViolationError as ssrf_err:
            latency_ms = (time.perf_counter() - start_time) * 1000
            evidence = EvidenceModel(
                source_url=current_url if 'current_url' in locals() else probe_url,
                evidence_type="ssrf_blocked",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.ERROR,
                confidence_score=0.0,
                response_time_ms=latency_ms,
                match_evidence=f"SSRF Protection prevented request/redirect: {ssrf_err}",
            )
            return SearchResult(
                site_name=site.name,
                category=site.category,
                target_username=username,
                status=VerificationStatus.ERROR,
                evidence=evidence,
                error_message=f"SSRF Protection: {ssrf_err}",
                latency_ms=latency_ms,
            )

        except httpx.TimeoutException:
            latency_ms = (time.perf_counter() - start_time) * 1000
            evidence = EvidenceModel(
                source_url=probe_url,
                evidence_type="timeout",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.INCONCLUSIVE,
                confidence_score=0.0,
                response_time_ms=latency_ms,
                match_evidence=f"Target timed out after {timeout_seconds}s.",
            )
            return SearchResult(
                site_name=site.name,
                category=site.category,
                target_username=username,
                status=VerificationStatus.INCONCLUSIVE,
                evidence=evidence,
                error_message="Probe request timed out",
                latency_ms=latency_ms,
            )

        except httpx.RequestError as req_err:
            latency_ms = (time.perf_counter() - start_time) * 1000
            evidence = EvidenceModel(
                source_url=probe_url,
                evidence_type="connection_error",
                detection_method=DetectionMethod.STATUS_CODE,
                verification_status=VerificationStatus.ERROR,
                confidence_score=0.0,
                response_time_ms=latency_ms,
                match_evidence=f"Network error: {type(req_err).__name__}",
            )
            return SearchResult(
                site_name=site.name,
                category=site.category,
                target_username=username,
                status=VerificationStatus.ERROR,
                evidence=evidence,
                error_message=str(req_err),
                latency_ms=latency_ms,
            )
        finally:
            if close_client:
                await client.aclose()

    async def search_username(
        self,
        username: str,
        categories: Optional[List[PlatformCategory]] = None,
        concurrency: int = 15,
        timeout_seconds: float = 8.0,
    ) -> AsyncIterator[SearchResult]:
        """
        Executes concurrent searches across matching sites and streams findings.
        """
        active_sites = [s for s in self._sites if s.is_active]
        if categories:
            active_sites = [s for s in active_sites if s.category in categories]

        semaphore = asyncio.Semaphore(concurrency)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=concurrency)
        
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False, limits=limits) as client:
            async def bounded_check(s: SiteDefinition) -> SearchResult:
                async with semaphore:
                    return await self.check_site(s, username, client=client, timeout_seconds=timeout_seconds)

            tasks = [asyncio.create_task(bounded_check(s)) for s in active_sites]
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                yield result

