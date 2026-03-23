"""Position-Aware Blending Strategy.

This module implements a position-aware blending strategy that dynamically
adjusts the fusion weights based on document rank position.

Reference: Docs/20-RerankEngine-Architecture.md Section 11.2
"""

from __future__ import annotations

from typing import Any

from ..core.ranker import BaseRankStrategy, ScoredDocument


class PositionAwareBlendingStrategy(BaseRankStrategy):
    """Position-aware blending strategy.

    Dynamically adjusts fusion weights based on document rank position.
    This approach recognizes that top-ranked documents from retrieval
    already have high confidence, while lower-ranked documents benefit
    more from reranker scores.

    Default blend ratios:
    - Rank 1-3: 75% retrieval / 25% reranker
    - Rank 4-10: 60% retrieval / 40% reranker
    - Rank 11+: 40% retrieval / 60% reranker

    Reference: Docs/20-RerankEngine-Architecture.md Section 11.2
    """

    def __init__(
        self,
        blend_ratios: dict[str, list[float]] | None = None,
    ):
        """Initialize PositionAwareBlendingStrategy.

        Args:
            blend_ratios: Custom blend ratios. Keys are rank ranges like
                "1-3", "4-10", "11+". Values are [retrieval_weight, reranker_weight].
                Default: {
                    "1-3": [0.75, 0.25],
                    "4-10": [0.60, 0.40],
                    "11+": [0.40, 0.60]
                }
        """
        self.blend_ratios = blend_ratios or {
            "1-3": [0.75, 0.25],
            "4-10": [0.60, 0.40],
            "11+": [0.40, 0.60],
        }

    @property
    def name(self) -> str:
        """Strategy name."""
        return "position_aware"

    def _get_blend_ratio(self, rank: int) -> list[float]:
        """Get blend ratio for a given rank.

        Args:
            rank: Document rank (1-based)

        Returns:
            [retrieval_weight, reranker_weight]
        """
        if rank <= 3:
            return self.blend_ratios.get("1-3", [0.75, 0.25])
        elif rank <= 10:
            return self.blend_ratios.get("4-10", [0.60, 0.40])
        else:
            return self.blend_ratios.get("11+", [0.40, 0.60])

    def rank(
        self,
        scored_docs: list[ScoredDocument],
        top_k: int | None = None,
        **kwargs: Any,
    ) -> list[ScoredDocument]:
        """Rank documents with position-aware blending.

        This method expects scored_docs to have additional attributes:
        - retrieval_score: Original retrieval score
        - rerank_score: Reranker score

        Args:
            scored_docs: Documents with scores
            top_k: Number of results to return
            **kwargs: Additional parameters (ignored)

        Returns:
            Ranked documents with blended scores
        """
        if not scored_docs:
            return []

        # Sort by rerank score first to get initial ranking
        sorted_docs = sorted(scored_docs, key=lambda d: d.score, reverse=True)

        blended_docs = []
        for rank, doc in enumerate(sorted_docs, 1):
            blend_ratio = self._get_blend_ratio(rank)
            retrieval_weight = blend_ratio[0]
            reranker_weight = blend_ratio[1]

            # Get scores (use doc.score as rerank_score if not separate)
            retrieval_score = getattr(doc, "retrieval_score", doc.score)
            rerank_score = getattr(doc, "rerank_score", doc.score)

            # Compute blended score
            blended_score = retrieval_weight * retrieval_score + reranker_weight * rerank_score

            # Create new document with blended score
            blended_doc = ScoredDocument(
                document_id=doc.document_id,
                text=doc.text,
                score=blended_score,
                metadata={
                    **doc.metadata,
                    "blend_ratio": blend_ratio,
                    "retrieval_score": retrieval_score,
                    "rerank_score": rerank_score,
                    "original_rank": rank,
                },
                original_index=doc.original_index,
            )
            blended_docs.append(blended_doc)

        # Re-sort by blended score
        blended_docs.sort(key=lambda d: d.score, reverse=True)

        # Apply top_k
        if top_k is not None:
            blended_docs = blended_docs[:top_k]

        return blended_docs

    def get_config(self) -> dict[str, Any]:
        """Get strategy configuration."""
        return {
            "name": self.name,
            "blend_ratios": self.blend_ratios,
        }
