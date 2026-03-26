"""Hybrid Scorer tests.

Tests for HybridFusionScorer with and without embedding provider.
"""

import pytest
from unittest.mock import MagicMock

from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer


class TestHybridScorer:
    """Tests for Hybrid scorer."""

    def test_hybrid_scorer_with_embedding_provider(self):
        """Test Hybrid scorer with embedding provider."""
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        scorer = HybridFusionScorer(embedding_provider=mock_provider)

        assert scorer._vector_scorer._embedding_provider is mock_provider
        assert scorer.name == "hybrid_fusion"

    def test_hybrid_scorer_fusion_methods(self):
        """Test different fusion methods."""
        # Linear fusion
        scorer_linear = HybridFusionScorer(fusion_method="linear")
        assert scorer_linear.fusion_method == "linear"

        # RRF fusion
        scorer_rrf = HybridFusionScorer(fusion_method="rrf")
        assert scorer_rrf.fusion_method == "rrf"

        # Weighted RRF
        scorer_wrrf = HybridFusionScorer(fusion_method="weighted_rrf")
        assert scorer_wrrf.fusion_method == "weighted_rrf"

    def test_hybrid_scorer_unknown_fusion(self):
        """Test unknown fusion method still works (uses linear default)."""
        # Should still instantiate with any fusion method
        scorer = HybridFusionScorer(fusion_method="unknown")
        assert scorer.fusion_method == "unknown"

    def test_hybrid_scorer_without_embedding(self):
        """Test Hybrid scorer fallback without embedding provider."""
        scorer = HybridFusionScorer(embedding_provider=None)

        # Should be able to instantiate
        assert scorer is not None
        assert scorer._vector_scorer._embedding_provider is None

        # Should use text-based fallback for vector component
        scores = scorer.compute_scores("test query", ["doc1", "doc2"])
        assert len(scores) == 2

    def test_hybrid_scorer_basic_scoring(self):
        """Test Hybrid scorer basic scoring."""
        scorer = HybridFusionScorer(
            vector_weight=0.7,
            fusion_method="linear",
        )

        query = "machine learning"
        documents = [
            "Machine learning is a subset of AI",
            "Python is a programming language",
            "Deep learning uses neural networks",
        ]

        scores = scorer.compute_scores(query, documents)

        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)

    def test_hybrid_scorer_empty_documents(self):
        """Test Hybrid scorer with empty documents."""
        scorer = HybridFusionScorer(embedding_provider=None)
        scores = scorer.compute_scores("query", [])
        assert len(scores) == 0

    def test_hybrid_scorer_empty_query(self):
        """Test Hybrid scorer with empty query."""
        scorer = HybridFusionScorer(embedding_provider=None)
        scores = scorer.compute_scores("", ["doc1", "doc2"])
        assert len(scores) == 2
        assert all(s == 0 for s in scores)

    def test_hybrid_scorer_batch_support(self):
        """Test Hybrid scorer supports batch processing."""
        scorer = HybridFusionScorer(embedding_provider=None)
        assert scorer.supports_batch is True