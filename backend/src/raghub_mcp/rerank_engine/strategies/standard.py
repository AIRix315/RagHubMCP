"""StandardRankStrategy - Standard score-based ranking.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4.3
"""

from __future__ import annotations

from typing import Any

from ..core.ranker import BaseRankStrategy, ScoredDocument


class StandardRankStrategy(BaseRankStrategy):
    """Standard ranking strategy.

    Ranks documents by score in descending order (highest first).
    This is the simplest and most common ranking approach.

    Example:
        >>> strategy = StandardRankStrategy()
        >>> ranked = strategy.rank(scored_docs, top_k=5)
    """

    @property
    def name(self) -> str:
        """Strategy name."""
        return "standard"

    def rank(
        self,
        scored_docs: list[ScoredDocument],
        top_k: int | None = None,
        **kwargs: Any,
    ) -> list[ScoredDocument]:
        """Rank documents by score descending.

        Args:
            scored_docs: Documents with computed scores.
            top_k: Maximum results to return. None returns all.
            **kwargs: Ignored for standard strategy.

        Returns:
            Documents sorted by score (highest first).
        """
        # Sort by score descending (uses __lt__ from ScoredDocument)
        sorted_docs = sorted(scored_docs)

        # Apply top_k limit
        if top_k is not None:
            return sorted_docs[:top_k]

        return sorted_docs

    def get_config(self) -> dict[str, Any]:
        """Get strategy configuration."""
        return {"name": self.name}
