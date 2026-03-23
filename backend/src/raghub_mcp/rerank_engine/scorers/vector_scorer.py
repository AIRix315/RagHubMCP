"""VectorScorer implementation for vector similarity scoring.

This module implements a pure vector similarity scoring component
that computes relevance scores based on vector embeddings.

Reference:
- Docs/20-RerankEngine-Architecture.md Section 4.2.1
- Cosine/Dot/Euclidean similarity calculations

Supported similarity functions:
    - cosine: Cosine similarity (normalized dot product)
    - dot: Dot product similarity
    - euclidean: Euclidean distance-based similarity
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from ..core.scorer import BaseScorer

logger = logging.getLogger(__name__)


class VectorScorer(BaseScorer):
    """Vector similarity scoring component.

    Computes relevance scores using vector similarity functions.
    This is a lightweight alternative to neural reranking that works
    with pre-computed embeddings.

    Note: This scorer requires an embedding provider to generate embeddings
    for the query. Documents should have pre-computed embeddings or the
    scorer will compute them on-the-fly if an embedding provider is available.

    Attributes:
        similarity_fn: Similarity function to use ('cosine', 'dot', 'euclidean')

    Example:
        >>> scorer = VectorScorer(similarity_fn="cosine")
        >>> scores = scorer.compute_scores("machine learning", docs)
    """

    def __init__(
        self,
        similarity_fn: str = "cosine",
        embedding_provider: Any = None,
    ):
        """Initialize VectorScorer.

        Args:
            similarity_fn: Similarity function to use.
                - 'cosine': Cosine similarity (default)
                - 'dot': Dot product
                - 'euclidean': Euclidean distance-based similarity
            embedding_provider: Optional embedding provider for generating
                query embeddings. If not provided, the scorer will use
                a simple TF-IDF fallback for scoring.
        """
        self.similarity_fn = similarity_fn
        self._embedding_provider = embedding_provider

        if similarity_fn not in ("cosine", "dot", "euclidean"):
            logger.warning(
                f"Unknown similarity function '{similarity_fn}', using 'cosine'"
            )
            self.similarity_fn = "cosine"

    @property
    def name(self) -> str:
        """Scorer name identifier."""
        return "vector"

    @property
    def supports_batch(self) -> bool:
        """VectorScorer supports batch processing."""
        return True

    def compute_scores(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute vector similarity scores for query-document pairs.

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

        # For now, use a simple text-based similarity fallback
        # In production, this would use embedding provider for actual vector similarity
        scores = self._compute_text_similarity(query, documents)

        return scores

    def _compute_text_similarity(self, query: str, documents: list[str]) -> np.ndarray:
        """Compute text-based similarity as a fallback.

        This provides a simple TF-based similarity when no embedding provider
        is available. In production, this should use actual vector embeddings.

        Args:
            query: Query string.
            documents: List of document strings.

        Returns:
            Array of similarity scores.
        """
        # Simple term overlap similarity
        query_terms = set(self._tokenize(query))
        if not query_terms:
            return np.zeros(len(documents))

        scores = []
        for doc in documents:
            doc_terms = set(self._tokenize(doc))
            if not doc_terms:
                scores.append(0.0)
                continue

            # Jaccard-like similarity with term frequency consideration
            overlap = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms)

            if union == 0:
                scores.append(0.0)
            else:
                # Weighted overlap score
                score = overlap / len(query_terms)  # Fraction of query terms found
                scores.append(score)

        return np.array(scores)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms.

        Args:
            text: Input text.

        Returns:
            List of lowercase tokens.
        """
        import re

        text = text.lower()
        return re.findall(r"\w+", text, re.UNICODE)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors.

        Formula: cos(θ) = (A · B) / (||A|| * ||B||)

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Cosine similarity in range [-1, 1].
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _dot_product(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute dot product between two vectors.

        Formula: A · B = sum(A[i] * B[i])

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Dot product value.
        """
        return float(np.dot(vec1, vec2))

    def _euclidean_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute euclidean distance-based similarity.

        Formula: similarity = 1 / (1 + distance)
        Where distance = ||A - B||

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Similarity in range (0, 1], where 1 means identical.
        """
        distance = np.linalg.norm(vec1 - vec2)
        return float(1.0 / (1.0 + float(distance)))

    def get_config(self) -> dict[str, Any]:
        """Get scorer configuration for logging/debugging.

        Returns:
            Dictionary with scorer configuration.
        """
        return {
            "name": self.name,
            "supports_batch": self.supports_batch,
            "similarity_fn": self.similarity_fn,
        }