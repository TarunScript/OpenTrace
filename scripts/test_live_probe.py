"""
Verification script for real username probe
Tests genuine public profiles against the Curated OSINT Engine.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.osint_engine.adapters.curated_adapter import CuratedOSINTAdapter
from packages.schemas import VerificationStatus, PlatformCategory


async def main():
    target = "torvalds"
    print(f"=== OpenTrace Live Probe Test: @{target} ===")
    adapter = CuratedOSINTAdapter()
    
    found_count = 0
    checked_count = 0

    async for result in adapter.search_username(target, categories=[PlatformCategory.DEVELOPER]):
        checked_count += 1
        status_symbol = "✓" if result.status == VerificationStatus.VERIFIED else "✗"
        print(f"[{status_symbol}] {result.site_name} ({result.category}): {result.status.value} (latency: {result.latency_ms:.1f}ms)")
        if result.profile:
            found_count += 1
            print(f"    - URL: {result.profile.profile_url}")
            print(f"    - Name: {result.profile.display_name}")
            print(f"    - Bio: {result.profile.biography[:60] if result.profile.biography else 'N/A'}...")
            print(f"    - Confidence: Existence={result.profile.confidence_existence}, Data={result.profile.confidence_data}")

    print(f"\nCompleted: {found_count} verified profiles found out of {checked_count} platforms checked.")
    assert found_count >= 1, "Expected at least 1 verified profile for known user"
    print("SUCCESS: Real OSINT probe verified!")


if __name__ == "__main__":
    asyncio.run(main())

