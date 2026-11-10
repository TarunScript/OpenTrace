import pytest
from packages.schemas import ProfileData, PlatformCategory
from packages.osint_engine.core.identity_resolver import IdentityResolver


def test_identity_resolver_matching_domains():
    p1 = ProfileData(
        platform="GitHub",
        username="tarun",
        profile_url="https://github.com/tarun",
        category=PlatformCategory.DEVELOPER,
        public_website="https://tarun.dev",
        confidence_existence=0.9,
        confidence_data=0.8,
    )
    p2 = ProfileData(
        platform="Dev.to",
        username="tarun",
        profile_url="https://dev.to/tarun",
        category=PlatformCategory.DEVELOPER,
        public_website="https://tarun.dev",
        confidence_existence=0.9,
        confidence_data=0.8,
    )

    graph = IdentityResolver.resolve_relationships("tarun", [p1, p2])
    assert len(graph.nodes) == 3 # 1 root + 2 profiles
    assert len(graph.edges) == 3 # 2 root-to-profile + 1 domain edge

    domain_edge = [e for e in graph.edges if e.relationship_type == "matching_domain"]
    assert len(domain_edge) == 1
    assert domain_edge[0].confidence_tier == "verified"
    assert domain_edge[0].confidence_score >= 0.90


def test_identity_resolver_cross_links():
    p1 = ProfileData(
        platform="GitHub",
        username="janedoe",
        profile_url="https://github.com/janedoe",
        category=PlatformCategory.DEVELOPER,
        biography="Open source dev. Check out my posts at reddit/janedoe",
        confidence_existence=0.95,
        confidence_data=0.85,
    )
    p2 = ProfileData(
        platform="Reddit",
        username="janedoe",
        profile_url="https://reddit.com/user/janedoe",
        category=PlatformCategory.FORUMS,
        biography="Software tinkerer.",
        confidence_existence=0.9,
        confidence_data=0.7,
    )

    graph = IdentityResolver.resolve_relationships("janedoe", [p1, p2])
    crosslink_edges = [e for e in graph.edges if e.relationship_type == "explicit_cross_link"]
    assert len(crosslink_edges) == 1
    assert crosslink_edges[0].confidence_tier == "verified"

