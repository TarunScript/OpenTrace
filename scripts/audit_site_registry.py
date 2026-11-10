"""
Comprehensive Audit Script: Inspects and Audits all OpenTrace Platform Definitions.
Tests both genuine ('torvalds') and nonexistent ('_opentrace_ghost_xyz9988_') targets.
Ensures every platform receives exactly one classification per audit:
  - Verified
  - Not found
  - Inconclusive
  - Error
Never classifies CAPTCHA, login walls, rate limits or blocked requests as Not Found.
Reports the evidence supporting every classification.
"""
import asyncio
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.osint_engine.adapters.curated_adapter import CuratedOSINTAdapter
from packages.schemas import VerificationStatus
from packages.site_registry.registry import default_registry, CURATED_SITES


async def audit_platforms():
    print("=" * 80)
    print("OPENTRACE PLATFORM REGISTRY AUDIT")
    print("=" * 80)

    sites = default_registry.list_all()
    total_sites = len(sites)
    print(f"\n1. REGISTERED PLATFORM INVENTORY: {total_sites} Total Unique Platforms\n")

    # Group by category
    by_category = defaultdict(list)
    for s in sorted(sites, key=lambda x: (x.category.value, x.name)):
        by_category[s.category.value].append(s.name)

    print("Platform Distribution by Category:")
    for cat, site_names in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  - {cat.capitalize():12} ({len(site_names):2} platforms): {', '.join(site_names)}")

    print(f"\nTotal Platforms Across Categories: {sum(len(v) for v in by_category.values())}")

    adapter = CuratedOSINTAdapter()

    # --- AUDIT RUN 1: Non-existent Target ---
    ghost_user = "_opentrace_ghost_xyz9988_"
    print(f"\n" + "=" * 80)
    print(f"AUDIT RUN 1: Negative Baseline Probe (Target: @{ghost_user})")
    print("Requirement: Must NEVER produce a VERIFIED classification on non-existent targets.")
    print("=" * 80)

    ghost_results = {}
    async for res in adapter.search_username(ghost_user, concurrency=8, timeout_seconds=6.0):
        ghost_results[res.site_name] = res

    # Table output
    print(f"{'Platform':16} | {'Classification':14} | {'Latency':8} | {'Evidence':40}")
    print("-" * 84)

    ghost_status_counts = defaultdict(int)
    false_positives = []

    for site in sorted(sites, key=lambda x: x.name):
        res = ghost_results.get(site.name)
        if res:
            status_val = res.status.value.upper()
            ghost_status_counts[status_val] += 1
            if res.status == VerificationStatus.VERIFIED:
                false_positives.append(site.name)
            ev_summary = res.evidence.match_evidence[:38] if res.evidence else "N/A"
            print(f"{site.name:16} | {status_val:14} | {res.latency_ms:6.1f}ms | {ev_summary:40}")

    print("-" * 84)
    print("Audit Run 1 Summary:")
    for stat, count in sorted(ghost_status_counts.items()):
        print(f"  - {stat:14}: {count:2} platforms")
    print(f"False Positives on Nonexistent Target: {len(false_positives)}")
    if false_positives:
        print(f"FAILED: Platforms falsely verifying nonexistent user: {false_positives}")
    else:
        print("PASSED: 0 False Positives on non-existent target!")

    # --- AUDIT RUN 2: Known Genuine Target ---
    real_user = "torvalds"
    print(f"\n" + "=" * 80)
    print(f"AUDIT RUN 2: Positive Signal Probe (Target: @{real_user})")
    print("Requirement: Classify genuine profile, absence, or inconclusive/rate limits with evidence.")
    print("=" * 80)

    real_results = {}
    async for res in adapter.search_username(real_user, concurrency=8, timeout_seconds=6.0):
        real_results[res.site_name] = res

    print(f"{'Platform':16} | {'Classification':14} | {'Latency':8} | {'Evidence':40}")
    print("-" * 84)

    real_status_counts = defaultdict(int)
    for site in sorted(sites, key=lambda x: x.name):
        res = real_results.get(site.name)
        if res:
            status_val = res.status.value.upper()
            real_status_counts[status_val] += 1
            ev_summary = res.evidence.match_evidence[:38] if res.evidence else "N/A"
            print(f"{site.name:16} | {status_val:14} | {res.latency_ms:6.1f}ms | {ev_summary:40}")

    print("-" * 84)
    print("Audit Run 2 Summary:")
    for stat, count in sorted(real_status_counts.items()):
        print(f"  - {stat:14}: {count:2} platforms")

    return ghost_status_counts, real_status_counts, len(false_positives)


if __name__ == "__main__":
    asyncio.run(audit_platforms())
