"""DiversityRankStrategy - MMR-based diverse ranking.

Reference: Docs/20-RerankEngine-Architecture.md Section 11.2
"""

from __future__ import annotations

from typing import Any

from ..core.ranker import BaseRankStrategy, ScoredDocument


class DiversityRankStrategy(BaseRankStrategy):
    """Diversity ranking strategy using MMR (Maximal Marginal Relevance).

    Promotes diversity in results by balancing relevance and novelty.
    Uses text similarity to identify similar documents and avoid
    returning too many similar results.

    Attributes:
        lambda_param: Balance between relevance (1.0) and diversity (0.0).

    Example:
        >>> strategy = DiversityRankStrategy(lambda_param=0.7)
        >>> ranked = strategy.rank(scored_docs, top_k=5)
    """

    def __init__(self, lambda_param: float = 0.5) -> None:
        """Initialize diversity strategy.

        Args:
            lambda_param: Balance between relevance and diversity.
                1.0 = pure relevance (same as standard)
                0.0 = pure diversity
                0.5 = balanced
        """
        self._lambda = lambda_param

    @property
    def name(self) -> str:
        """Strategy name."""
        return "diversity"

    @property
    def lambda_param(self) -> float:
        """Get lambda parameter."""
        return self._lambda

    def rank(
        self,
        scored_docs: list[ScoredDocument],
        top_k: int | None = None,
        **kwargs: Any,
    ) -> list[ScoredDocument]:
        """Rank documents with diversity using MMR.

        Args:
            scored_docs: Documents with computed scores.
            top_k: Maximum results to return.
            **kwargs: Additional parameters.

        Returns:
            Diversified documents sorted by MMR score.
        """
        if not scored_docs:
            return []

        n = len(scored_docs)
        k = min(top_k, n) if top_k else n

        if k >= n:
            # If we need all documents, just sort by score
            return sorted(scored_docs)

        # Simple MMR implementation
        # Start with highest scored document
        sorted_by_score = sorted(scored_docs)
        selected = [sorted_by_score[0]]
        remaining = sorted_by_score[1:]

        while len(selected) < k and remaining:
            best_mmr = -float("inf")
            best_idx = 0

            for i, doc in enumerate(remaining):
                # Relevance component
                relevance = doc.score

                # Diversity component (max similarity to selected docs)
                max_sim = self._max_similarity(doc, selected)

                # MMR score
                mmr = self._lambda * relevance - (1 - self._lambda) * max_sim

                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    def _max_similarity(
        self, doc: ScoredDocument, selected: list[ScoredDocument]
    ) -> float:
        """Calculate maximum similarity to selected documents.

        Uses simple word overlap for text similarity.
        For better results, use embedding-based similarity.
        """
        if not selected:
            return 0.0

        doc_words = set(doc.text.lower().split())
        max_sim = 0.0

        for selected_doc in selected:
            selected_words = set(selected_doc.text.lower().split())

            # Jaccard similarity
            if not doc_words or not selected_words:
                sim = 0.0
            else:
                intersection = len(doc_words & selected_words)
                union = len(doc_words | selected_words)
                sim = intersection / union if union > 0 else 0.0

            max_sim = max(max_sim, sim)

        return max_sim

    def get_config(self) -> dict[str, Any]:
        """Get strategy configuration."""
        return {
            "name": self.name,
            "lambda_param": self._lambda,
        }