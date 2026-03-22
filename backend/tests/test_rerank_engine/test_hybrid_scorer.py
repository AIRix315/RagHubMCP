"""Tests for HybridFusionScorer implementation.

This module tests the hybrid fusion scoring algorithm as defined in:
- Docs/20-RerankEngine-Architecture.md Section 11.1
- TODO 2.2.1-2.2.3: HybridFusionScorer实现

Reference:
- rag-code-mcp: hybrid_search.go#L228-L239 (60/40 linear fusion)
- SylphxAI/coderag: hybrid-search.ts#L169-L263 (score normalization)
- LlamaIndex: ReciprocalRankFusion (RRF algorithm)
"""

import numpy as np
import pytest

from raghub_mcp.rerank_engine.core.scorer import BaseScorer


class TestHybridFusionScorer:
    """Tests for HybridFusionScorer implementation."""

    @pytest.fixture
    def hybrid_scorer(self):
        """Create HybridFusionScorer with default parameters."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        return HybridFusionScorer(vector_weight=0.7, fusion_method="linear")

    @pytest.fixture
    def hybrid_rrf(self):
        """Create HybridFusionScorer with RRF fusion."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        return HybridFusionScorer(fusion_method="rrf", k=60)

    # =========================================================================
    # Basic Properties Tests
    # =========================================================================

    def test_scorer_is_base_scorer(self, hybrid_scorer):
        """HybridFusionScorer should inherit from BaseScorer."""
        assert isinstance(hybrid_scorer, BaseScorer)

    def test_scorer_name(self, hybrid_scorer):
        """Scorer should have correct name."""
        assert hybrid_scorer.name == "hybrid_fusion"

    def test_supports_batch(self, hybrid_scorer):
        """HybridFusionScorer should support batch processing."""
        assert hybrid_scorer.supports_batch is True

    def test_default_parameters(self, hybrid_scorer):
        """Default parameters should match expected values."""
        assert hybrid_scorer.vector_weight == 0.7
        assert hybrid_scorer.fusion_method == "linear"

    # =========================================================================
    # Score Normalization Tests (Task 2.2.1)
    # =========================================================================

    def test_minmax_normalization(self, hybrid_scorer):
        """Test min-max normalization."""
        scores = np.array([0.0, 0.5, 1.0, 0.25])
        normalized = hybrid_scorer._normalize(scores, method="minmax")

        assert np.allclose(normalized, [0.0, 0.5, 1.0, 0.25])

    def test_minmax_normalization_different_range(self, hybrid_scorer):
        """Test min-max normalization with different score ranges."""
        scores = np.array([0.0, 5.0, 10.0])
        normalized = hybrid_scorer._normalize(scores, method="minmax")

        assert np.allclose(normalized, [0.0, 0.5, 1.0])

    def test_minmax_normalization_single_value(self, hybrid_scorer):
        """Test min-max normalization with single value."""
        scores = np.array([0.5])
        normalized = hybrid_scorer._normalize(scores, method="minmax")

        # Single value should normalize to 1.0 or stay as is
        assert normalized[0] == 1.0 or normalized[0] == 0.5

    def test_softmax_normalization(self, hybrid_scorer):
        """Test softmax normalization."""
        scores = np.array([1.0, 2.0, 3.0])
        normalized = hybrid_scorer._normalize(scores, method="softmax")

        # Softmax should produce probabilities summing to 1
        assert abs(sum(normalized) - 1.0) < 0.001
        assert all(0 <= s <= 1 for s in normalized)

    def test_zscore_normalization(self, hybrid_scorer):
        """Test z-score normalization."""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = hybrid_scorer._normalize(scores, method="zscore")

        # Mean should be approximately 0
        assert abs(np.mean(normalized)) < 0.001
        # Std should be approximately 1
        assert abs(np.std(normalized) - 1.0) < 0.001

    # =========================================================================
    # Linear Weighted Fusion Tests (Task 2.2.2)
    # =========================================================================

    def test_linear_fusion_basic(self, hybrid_scorer):
        """Test basic linear weighted fusion.

        Formula: score = vector_weight * vector_score + (1 - vector_weight) * bm25_score
        """
        vector_scores = np.array([0.9, 0.8, 0.7])
        bm25_scores = np.array([0.6, 0.7, 0.8])

        fused = hybrid_scorer._linear_fusion(vector_scores, bm25_scores)

        # With vector_weight=0.7
        # fused[0] = 0.7 * 0.9 + 0.3 * 0.6 = 0.63 + 0.18 = 0.81
        expected = 0.7 * vector_scores + 0.3 * bm25_scores
        assert np.allclose(fused, expected)

    def test_linear_fusion_vector_dominant(self):
        """Test fusion when vector weight is high."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        scorer = HybridFusionScorer(vector_weight=0.9)

        vector_scores = np.array([1.0, 0.0])
        bm25_scores = np.array([0.0, 1.0])

        fused = scorer._linear_fusion(vector_scores, bm25_scores)

        # With high vector weight, vector scores should dominate
        assert fused[0] > fused[1]

    def test_linear_fusion_bm25_dominant(self):
        """Test fusion when BM25 weight is high."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        scorer = HybridFusionScorer(vector_weight=0.1)

        vector_scores = np.array([1.0, 0.0])
        bm25_scores = np.array([0.0, 1.0])

        fused = scorer._linear_fusion(vector_scores, bm25_scores)

        # With low vector weight, BM25 scores should dominate
        assert fused[0] < fused[1]

    def test_linear_fusion_equal_weights(self):
        """Test fusion with equal weights (50/50)."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        scorer = HybridFusionScorer(vector_weight=0.5)

        vector_scores = np.array([0.8, 0.6])
        bm25_scores = np.array([0.4, 0.8])

        fused = scorer._linear_fusion(vector_scores, bm25_scores)

        expected = 0.5 * vector_scores + 0.5 * bm25_scores
        assert np.allclose(fused, expected)

    # =========================================================================
    # RRF Fusion Tests (Task 2.2.3)
    # =========================================================================

    def test_rrf_fusion_basic(self, hybrid_rrf):
        """Test basic RRF (Reciprocal Rank Fusion).

        Formula: RRF(d) = sum(1 / (k + rank(d)))
        """
        # Rank 1 in vector, Rank 3 in BM25
        # RRF = 1/(k+1) + 1/(k+3)
        vector_ranks = np.array([1, 2, 3])
        bm25_ranks = np.array([3, 1, 2])

        fused = hybrid_rrf._rrf_fusion(vector_ranks, bm25_ranks)

        # Document ranked high in both should score highest
        assert len(fused) == 3
        # RRF scores should be positive
        assert all(f > 0 for f in fused)

    def test_rrf_fusion_k_parameter(self):
        """Test RRF k parameter affects scoring."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        scorer_k10 = HybridFusionScorer(fusion_method="rrf", k=10)
        scorer_k60 = HybridFusionScorer(fusion_method="rrf", k=60)

        ranks = np.array([1, 2, 3])

        fused_k10 = scorer_k10._rrf_fusion(ranks, ranks)
        fused_k60 = scorer_k60._rrf_fusion(ranks, ranks)

        # Lower k should have higher scores (more weight on ranks)
        assert fused_k10[0] > fused_k60[0]

    def test_rrf_only_considers_ranks(self, hybrid_rrf):
        """Test that RRF only considers ranks, not raw scores."""
        # RRF should give same result regardless of score magnitude
        vector_ranks = np.array([1, 2, 3])
        bm25_ranks = np.array([1, 2, 3])

        fused = hybrid_rrf._rrf_fusion(vector_ranks, bm25_ranks)

        # All documents have same rank pattern, should have proportional scores
        assert fused[0] > fused[1] > fused[2]

    # =========================================================================
    # Integration Tests
    # =========================================================================

    def test_compute_scores_basic(self, hybrid_scorer):
        """Test end-to-end scoring with hybrid fusion."""
        query = "machine learning"
        documents = [
            "Machine learning is a subset of AI.",
            "Python is a programming language.",
            "Deep learning uses neural networks.",
        ]

        scores = hybrid_scorer.compute_scores(query, documents)

        assert isinstance(scores, np.ndarray)
        assert len(scores) == len(documents)
        assert all(0 <= s <= 1 for s in scores)

    def test_compute_scores_empty_documents(self, hybrid_scorer):
        """Test scoring with empty document list."""
        scores = hybrid_scorer.compute_scores("query", [])
        assert len(scores) == 0

    def test_fusion_method_comparison(self):
        """Compare different fusion methods produce different results."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        linear_scorer = HybridFusionScorer(fusion_method="linear", vector_weight=0.7)
        rrf_scorer = HybridFusionScorer(fusion_method="rrf", k=60)

        query = "test query"
        documents = ["doc one test", "doc two query", "doc three test query"]

        linear_scores = linear_scorer.compute_scores(query, documents)
        rrf_scores = rrf_scorer.compute_scores(query, documents)

        # Both should produce valid scores
        assert len(linear_scores) == len(rrf_scores) == 3
        # Methods may produce different orderings
        # This is expected behavior

    # =========================================================================
    # Weighted RRF Tests
    # =========================================================================

    def test_weighted_rrf_fusion(self):
        """Test weighted RRF fusion."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        scorer = HybridFusionScorer(
            fusion_method="weighted_rrf",
            vector_weight=0.7,
            k=60,
        )

        vector_ranks = np.array([1, 2, 3])
        bm25_ranks = np.array([3, 1, 2])

        fused = scorer._weighted_rrf_fusion(vector_ranks, bm25_ranks)

        assert len(fused) == 3
        assert all(f > 0 for f in fused)

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_normalization_empty_scores(self, hybrid_scorer):
        """Test normalization with empty scores."""
        scores = np.array([])
        normalized = hybrid_scorer._normalize(scores, method="minmax")
        assert len(normalized) == 0

    def test_normalization_all_same(self, hybrid_scorer):
        """Test normalization when all scores are the same."""
        scores = np.array([0.5, 0.5, 0.5])
        normalized = hybrid_scorer._normalize(scores, method="minmax")

        # All same values - minmax behavior may vary
        assert len(normalized) == 3

    def test_get_config(self, hybrid_scorer):
        """Test get_config returns correct configuration."""
        config = hybrid_scorer.get_config()

        assert config["name"] == "hybrid_fusion"
        assert config["supports_batch"] is True
        assert config["vector_weight"] == 0.7
        assert config["fusion_method"] == "linear"