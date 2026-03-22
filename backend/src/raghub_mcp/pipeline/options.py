"""Pipeline options for configuring RAG execution.

This module defines the PipelineOptions dataclass for configuring
pipeline behavior.

Reference:
- Docs/11-V2-Desing.md (Section 4)
- Docs/12-V2-Blueprint.md (Module 1)
- RULE.md (RULE-4: 所有能力必须可配置)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PipelineOptions:
    """Options for RAG pipeline execution.

    Attributes:
        collection: Collection name to query.
        topK: Number of results to return.
        rerank: Whether to apply reranking.
        rerank_provider: Name of rerank provider to use.
        embedding_provider: Name of embedding provider to use.
        where: Metadata filter for vector search.
        where_document: Document content filter.
        profile: Profile name (fast/balanced/accurate).
        alpha: Weight for vector search (hybrid).
        beta: Weight for BM25 search (hybrid).
    """

    collection: str = "default"
    top_k: int = 5
    rerank: bool = True
    rerank_provider: str | None = None
    embedding_provider: str | None = None
    where: dict[str, Any] | None = None
    where_document: dict[str, Any] | None = None
    profile: str = "balanced"
    alpha: float = 0.5
    beta: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for pipeline.run()."""
        return {
            "collection": self.collection,
            "topK": self.top_k,
            "rerank": self.rerank,
            "rerank_provider": self.rerank_provider,
            "embedding_provider": self.embedding_provider,
            "where": self.where,
            "where_document": self.where_document,
            "profile": self.profile,
            "alpha": self.alpha,
            "beta": self.beta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineOptions:
        """Create from dictionary.

        Args:
            data: Dictionary with option values.

        Returns:
            PipelineOptions instance.
        """
        return cls(
            collection=data.get("collection", "default"),
            top_k=data.get("topK", data.get("top_k", 5)),
            rerank=data.get("rerank", True),
            rerank_provider=data.get("rerank_provider"),
            embedding_provider=data.get("embedding_provider"),
            where=data.get("where"),
            where_document=data.get("where_document"),
            profile=data.get("profile", "balanced"),
            alpha=data.get("alpha", 0.5),
            beta=data.get("beta", 0.5),
        )

    @classmethod
    def from_request(cls, request: Any) -> PipelineOptions:
        """Create from API request object.

        Args:
            request: SearchRequest or similar object.

        Returns:
            PipelineOptions instance.
        """
        return cls(
            collection=getattr(request, "collection_name", "default"),
            top_k=getattr(request, "top_k", getattr(request, "topK", 5)),
            rerank=getattr(request, "use_rerank", True),
            rerank_provider=getattr(request, "rerank_provider", None),
            embedding_provider=getattr(request, "embedding_provider", None),
            where=getattr(request, "where", None),
            where_document=getattr(request, "where_document", None),
            profile="balanced",
            alpha=0.5,
            beta=0.5,
        )
