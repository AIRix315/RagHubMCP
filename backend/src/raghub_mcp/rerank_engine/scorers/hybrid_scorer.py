"""HybridFusionScorer implementation for hybrid search scoring.

This module implements a hybrid fusion scoring algorithm that combines
BM25 lexical matching with vector semantic similarity.

Reference:
- Docs/20-RerankEngine-Architecture.md Section 11.1
- rag-code-mcp: hybrid_search.go#L228-L239 (60/40 linear fusion)
- SylphxAI/coderag: hybrid-search.ts#L169-L263 (score normalization)
- LlamaIndex: ReciprocalRankFusion (RRF algorithm)

Supported fusion methods:
    - linear: Weighted linear combination of scores
    - rrf: Reciprocal Rank Fusion
    - weighted_rrf: Weighted combination using RRF scores
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import numpy as np

from ..core.scorer import BaseScorer
from .bm25_scorer import BM25Scorer
from .vector_scorer import VectorScorer

logger = logging.getLogger(__name__)


class HybridFusionScorer(BaseScorer):
    """Hybrid fusion scoring component.

    Combines BM25 lexical matching with vector semantic similarity
    to provide a lightweight alternative to neural reranking.

    This scorer is particularly effective for:
    - Code search (precise term matching + semantic understanding)
    - Resource-constrained environments (no neural model required)
    - Scenarios where both keyword and semantic relevance matter

    Attributes:
        vector_weight: Weight for vector scores in linear fusion (default 0.7)
        fusion_method: Fusion method ('linear', 'rrf', 'weighted_rrf')
        k: RRF k parameter (default 60)

    Example:
        >>> scorer = HybridFusionScorer(vector_weight=0.7, fusion_method="linear")
        >>> scores = scorer.compute_scores("machine learning", docs)
    """

    def __init__(
        self,
        vector_weight: float = 0.7,
        fusion_method: Literal["linear", "rrf", "weighted_rrf"] = "linear",
        k: int = 60,
        normalize_method: Literal["minmax", "softmax", "zscore"] = "minmax",
        bm25_config: dict[str, Any] | None = None,
    ):
        """Initialize HybridFusionScorer.

        Args:
            vector_weight: Weight for vector scores in fusion (0-1).
                Higher values prioritize semantic similarity. Default 0.7.
            fusion_method: Method for combining scores:
                - 'linear': Weighted linear combination
                - 'rrf': Reciprocal Rank Fusion
                - 'weighted_rrf': Weighted RRF combining both
            k: RRF k parameter. Higher values smooth the rank effect. Default 60.
            normalize_method: Method for normalizing scores before fusion:
                - 'minmax': Min-max normalization (default)
                - 'softmax': Softmax normalization
                - 'zscore': Z-score normalization
            bm25_config: Optional configuration for BM25Scorer.
        """
        self.vector_weight = vector_weight
        self.fusion_method = fusion_method
        self.k = k
        self.normalize_method = normalize_method

        # Initialize sub-scorers
        bm25_cfg = bm25_config or {}
        self._bm25_scorer = BM25Scorer(**bm25_cfg)
        self._vector_scorer = VectorScorer()

        logger.debug(
            f"HybridFusionScorer initialized: method={fusion_method}, "
            f"vector_weight={vector_weight}, k={k}"
        )

    @property
    def name(self) -> str:
        """Scorer name identifier."""
        return "hybrid_fusion"

    @property
    def supports_batch(self) -> bool:
        """HybridFusionScorer supports batch processing."""
        return True

    def compute_scores(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute hybrid fusion scores for query-document pairs.

        The scoring process:
        1. Compute BM25 scores
        2. Compute vector similarity scores
        3. Normalize both score sets
        4. Fuse scores using the selected method

        Args:
            query: The search query string.
            documents: List of document texts to score.

        Returns:
            NumPy array of shape (len(documents),) with scores in [0, 1].
        """
        if not documents:
            return np.array([])

        if not query or not query.strip():
            return np.zeros(len(documents))

        # Compute individual scores
        bm25_scores = self._bm25_scorer.compute_scores(query, documents)
        vector_scores = self._vector_scorer.compute_scores(query, documents)

        # Normalize scores
        bm25_normalized = self._normalize(bm25_scores, method=self.normalize_method)
        vector_normalized = self._normalize(vector_scores, method=self.normalize_method)

        # Fuse scores
        if self.fusion_method == "linear":
            fused = self._linear_fusion(vector_normalized, bm25_normalized)
        elif self.fusion_method == "rrf":
            # Convert scores to ranks for RRF
            vector_ranks = self._scores_to_ranks(vector_scores)
            bm25_ranks = self._scores_to_ranks(bm25_scores)
            fused = self._rrf_fusion(vector_ranks, bm25_ranks)
        elif self.fusion_method == "weighted_rrf":
            vector_ranks = self._scores_to_ranks(vector_scores)
            bm25_ranks = self._scores_to_ranks(bm25_scores)
            fused = self._weighted_rrf_fusion(vector_ranks, bm25_ranks)
        else:
            # Default to linear
            fused = self._linear_fusion(vector_normalized, bm25_normalized)

        # Final normalization
        fused = self._normalize(fused, method="minmax")

        return fused

    def _normalize(self, scores: np.ndarray, method: str = "minmax") -> np.ndarray:
        """Normalize scores using the specified method.

        Args:
            scores: Input scores.
            method: Normalization method ('minmax', 'softmax', 'zscore').

        Returns:
            Normalized scores.
        """
        if len(scores) == 0:
            return scores

        if method == "minmax":
            min_val = np.min(scores)
            max_val = np.max(scores)
            if max_val == min_val:
                return np.ones_like(scores) if max_val > 0 else np.zeros_like(scores)
            return (scores - min_val) / (max_val - min_val)

        elif method == "softmax":
            # Stable softmax
            exp_scores = np.exp(scores - np.max(scores))
            return exp_scores / np.sum(exp_scores)

        elif method == "zscore":
            mean = np.mean(scores)
            std = np.std(scores)
            if std == 0:
                return np.zeros_like(scores)
            return (scores - mean) / std

        else:
            # Default to minmax
            return self._normalize(scores, method="minmax")

    def _linear_fusion(
        self, vector_scores: np.ndarray, bm25_scores: np.ndarray
    ) -> np.ndarray:
        """Linear weighted fusion of scores.

        Formula: fused = vector_weight * vector + (1 - vector_weight) * bm25

        Args:
            vector_scores: Normalized vector similarity scores.
            bm25_scores: Normalized BM25 scores.

        Returns:
            Fused scores.
        """
        return self.vector_weight * vector_scores + (1 - self.vector_weight) * bm25_scores

    def _scores_to_ranks(self, scores: np.ndarray) -> np.ndarray:
        """Convert scores to ranks (1-based, lower is better).

        Args:
            scores: Input scores.

        Returns:
            1-based ranks array.
        """
        # Get indices that would sort the array in descending order
        sorted_indices = np.argsort(-scores)
        ranks = np.empty_like(sorted_indices)
        ranks[sorted_indices] = np.arange(1, len(scores) + 1)
        return ranks

    def _rrf_fusion(self, vector_ranks: np.ndarray, bm25_ranks: np.ndarray) -> np.ndarray:
        """Reciprocal Rank Fusion.

        Formula: RRF(d) = 1/(k + rank1) + 1/(k + rank2)

        Args:
            vector_ranks: Vector-based ranks (1-based).
            bm25_ranks: BM25-based ranks (1-based).

        Returns:
            RRF fusion scores.
        """
        return 1.0 / (self.k + vector_ranks) + 1.0 / (self.k + bm25_ranks)

    def _weighted_rrf_fusion(
        self, vector_ranks: np.ndarray, bm25_ranks: np.ndarray
    ) -> np.ndarray:
        """Weighted Reciprocal Rank Fusion.

        Formula: RRF(d) = w/(k + rank1) + (1-w)/(k + rank2)

        Args:
            vector_ranks: Vector-based ranks (1-based).
            bm25_ranks: BM25-based ranks (1-based).

        Returns:
            Weighted RRF fusion scores.
        """
        return (self.vector_weight / (self.k + vector_ranks)) + (
            (1 - self.vector_weight) / (self.k + bm25_ranks)
        )

    def get_config(self) -> dict[str, Any]:
        """Get scorer configuration for logging/debugging.

        Returns:
            Dictionary with scorer configuration.
        """
        return {
            "name": self.name,
            "supports_batch": self.supports_batch,
            "vector_weight": self.vector_weight,
            "fusion_method": self.fusion_method,
            "k": self.k,
            "normalize_method": self.normalize_method,
        }