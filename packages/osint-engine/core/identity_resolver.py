"""
Identity Resolution and Graph Correlation Engine
Evaluates relationships between discovered profiles based on tangible public evidence.
Produces nodes and edges for React Flow visualization with tiered relationship confidence.
"""
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from pydantic import BaseModel
from packages.schemas import ProfileData, VerificationStatus


class RelationshipEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str        # "explicit_cross_link", "matching_domain", "matching_display_name", "exact_username"
    confidence_tier: str          # "verified", "strongly_supported", "possible", "unverified"
    confidence_score: float       # 0.0 - 1.0
    evidence_reason: str


class GraphNode(BaseModel):
    id: str
    type: str                     # "query_target" or "profile"
    label: str
    platform: Optional[str] = None
    category: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    confidence_existence: float = 0.0
    confidence_data: float = 0.0
    status: str = "verified"


class InvestigationGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[RelationshipEdge]


class IdentityResolver:
    """
    Correlates discovered profiles using evidence-weighted similarity rules.
    """

    @classmethod
    def _normalize_domain(cls, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            # Ignore mega-domains that aren't personal identifiers
            if netloc in ("github.com", "twitter.com", "x.com", "reddit.com", "instagram.com", "t.me", "linkedin.com", "medium.com"):
                return None
            return netloc if netloc else None
        except Exception:
            return None

    @classmethod
    def resolve_relationships(
        cls,
        target_username: str,
        profiles: List[ProfileData],
    ) -> InvestigationGraph:
        """
        Builds the relationship graph for all discovered profiles.
        Root node is target_username.
        """
        nodes: List[GraphNode] = []
        edges: List[RelationshipEdge] = []

        # 1. Add root target node
        root_id = f"target_{target_username}"
        nodes.append(
            GraphNode(
                id=root_id,
                type="query_target",
                label=f"@{target_username}",
                platform="Query Target",
                category="target",
                status="verified",
                confidence_existence=1.0,
                confidence_data=1.0,
            )
        )

        # 2. Add profile nodes and root edges
        for idx, p in enumerate(profiles):
            node_id = f"p_{p.platform.lower()}_{idx}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type="profile",
                    label=p.display_name or f"{p.platform}/@{p.username}",
                    platform=p.platform,
                    category=p.category.value,
                    profile_url=p.profile_url,
                    avatar_url=p.profile_image_url,
                    confidence_existence=p.confidence_existence,
                    confidence_data=p.confidence_data,
                    status="verified",
                )
            )

            # Connect profile to root target (exact username match)
            edges.append(
                RelationshipEdge(
                    id=f"edge_root_{node_id}",
                    source=root_id,
                    target=node_id,
                    relationship_type="exact_username",
                    confidence_tier="strongly_supported" if p.confidence_existence >= 0.75 else "possible",
                    confidence_score=round(p.confidence_existence * 0.8, 2),
                    evidence_reason=f"Account claimed exact handle @{target_username} on {p.platform}.",
                )
            )

        # 3. Inter-profile correlation (cross-linking & matching attributes)
        n = len(profiles)
        for i in range(n):
            for j in range(i + 1, n):
                p1 = profiles[i]
                p2 = profiles[j]
                id1 = f"p_{p1.platform.lower()}_{i}"
                id2 = f"p_{p2.platform.lower()}_{j}"

                # A. Matching Custom Domain
                d1 = cls._normalize_domain(p1.public_website)
                d2 = cls._normalize_domain(p2.public_website)
                if d1 and d2 and d1 == d2:
                    edges.append(
                        RelationshipEdge(
                            id=f"edge_domain_{id1}_{id2}",
                            source=id1,
                            target=id2,
                            relationship_type="matching_domain",
                            confidence_tier="verified",
                            confidence_score=0.95,
                            evidence_reason=f"Both profiles publish identical personal domain: {d1}",
                        )
                    )
                    continue

                # B. Explicit Cross-Link (p1 bio contains p2 platform or vice versa)
                p2_host = p2.platform.lower()
                p1_host = p1.platform.lower()
                bio1 = (p1.biography or "").lower()
                bio2 = (p2.biography or "").lower()

                cross_linked = False
                if p2_host in bio1 and target_username.lower() in bio1:
                    cross_linked = True
                elif p1_host in bio2 and target_username.lower() in bio2:
                    cross_linked = True

                if cross_linked:
                    edges.append(
                        RelationshipEdge(
                            id=f"edge_crosslink_{id1}_{id2}",
                            source=id1,
                            target=id2,
                            relationship_type="explicit_cross_link",
                            confidence_tier="verified",
                            confidence_score=0.98,
                            evidence_reason=f"Explicit public cross-reference discovered between {p1.platform} and {p2.platform}.",
                        )
                    )
                    continue

                # C. Matching Rare Display Name
                if (
                    p1.display_name
                    and p2.display_name
                    and len(p1.display_name) > 3
                    and p1.display_name.lower() == p2.display_name.lower()
                    and p1.display_name.lower() != target_username.lower()
                ):
                    edges.append(
                        RelationshipEdge(
                            id=f"edge_name_{id1}_{id2}",
                            source=id1,
                            target=id2,
                            relationship_type="matching_display_name",
                            confidence_tier="strongly_supported",
                            confidence_score=0.75,
                            evidence_reason=f"Both profiles share identical display name: '{p1.display_name}'",
                        )
                    )

        return InvestigationGraph(nodes=nodes, edges=edges)

