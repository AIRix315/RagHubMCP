"""Vector Scorer tests.

Tests for VectorScorer with and without embedding provider.
"""

import pytest
from unittest.mock import MagicMock

from raghub_mcp.rerank_engine.scorers.vector_scorer import VectorScorer


class TestVectorScorer:
    """Tests for Vector scorer."""

    def test_vector_scorer_with_embedding_provider(self):
        """Test Vector scorer with embedding provider."""
        # Mock embedding provider
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        scorer = VectorScorer(embedding_provider=mock_provider)

        assert scorer._embedding_provider is mock_provider
        assert scorer.name == "vector"

    def test_vector_scorer_similarity_functions(self):
        """Test different similarity functions."""
        # Cosine similarity
        scorer_cosine = VectorScorer(similarity_fn="cosine")
        assert scorer_cosine.similarity_fn == "cosine"

        # Dot product
        scorer_dot = VectorScorer(similarity_fn="dot")
        assert scorer_dot.similarity_fn == "dot"

        # Euclidean
        scorer_euclidean = VectorScorer(similarity_fn="euclidean")
        assert scorer_euclidean.similarity_fn == "euclidean"

    def test_vector_scorer_unknown_similarity(self):
        """Test unknown similarity function defaults to cosine."""
        scorer = VectorScorer(similarity_fn="unknown")
        assert scorer.similarity_fn == "cosine"

    def test_vector_scorer_without_embedding(self):
        """Test Vector scorer fallback without embedding provider."""
        scorer = VectorScorer(embedding_provider=None)

        # Should be able to instantiate
        assert scorer is not None
        assert scorer._embedding_provider is None

        # Should use text-based fallback
        scores = scorer.compute_scores("test query", ["doc1", "doc2", "doc3"])
        assert len(scores) == 3

    def test_vector_scorer_empty_documents(self):
        """Test Vector scorer with empty documents."""
        scorer = VectorScorer(embedding_provider=None)
        scores = scorer.compute_scores("query", [])
        assert len(scores) == 0

    def test_vector_scorer_empty_query(self):
        """Test Vector scorer with empty query."""
        scorer = VectorScorer(embedding_provider=None)
        scores = scorer.compute_scores("", ["doc1", "doc2"])
        assert len(scores) == 2
        # All scores should be zero for empty query
        assert all(s == 0 for s in scores)

    def test_vector_scorer_batch_support(self):
        """Test Vector scorer supports batch processing."""
        scorer = VectorScorer(embedding_provider=None)
        assert scorer.supports_batch is True