"""Tests for scoring utility functions."""

import pytest

from src.utils.scoring import (
    distance_to_score,
    normalize_scores,
    reciprocal_rank_fusion,
)


class TestReciprocalRankFusion:
    """Tests for RRF algorithm."""

    def test_rrf_basic(self):
        """Test basic RRF fusion."""
        vector_results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        bm25_results = [("doc2", 0.95), ("doc1", 0.85), ("doc4", 0.6)]

        fused = reciprocal_rank_fusion(vector_results, bm25_results)

        # Should be sorted by score descending
        assert len(fused) == 4  # 4 unique docs
        # Doc1 and doc2 appear in both, should have higher scores
        doc_ids = [doc_id for doc_id, _ in fused]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids

    def test_rrf_empty_results(self):
        """Test RRF with empty results."""
        fused = reciprocal_rank_fusion([], [])
        assert fused == []

    def test_rrf_single_result(self):
        """Test RRF with single result."""
        fused = reciprocal_rank_fusion([("doc1", 0.9)], [])
        assert len(fused) == 1
        assert fused[0][0] == "doc1"

    def test_rrf_weights(self):
        """Test RRF with custom weights."""
        # Different rankings to test weight effect
        vector_results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        bm25_results = [("doc3", 0.95), ("doc1", 0.85), ("doc2", 0.6)]

        fused_alpha_high = reciprocal_rank_fusion(vector_results, bm25_results, alpha=0.9, beta=0.1)
        fused_beta_high = reciprocal_rank_fusion(vector_results, bm25_results, alpha=0.1, beta=0.9)

        # With alpha_high, doc1 (rank 1 in vector) should rank higher
        # With beta_high, doc3 (rank 1 in bm25) should rank higher
        alpha_top = fused_alpha_high[0][0]
        beta_top = fused_beta_high[0][0]

        # Different top documents due to different weights
        assert alpha_top != beta_top

    def test_rrf_custom_k(self):
        """Test RRF with custom k parameter."""
        vector_results = [("doc1", 0.9), ("doc2", 0.8)]
        bm25_results = [("doc2", 0.95), ("doc1", 0.85)]

        fused_default = reciprocal_rank_fusion(vector_results, bm25_results, k=60)
        fused_custom = reciprocal_rank_fusion(vector_results, bm25_results, k=10)

        # Different k should produce different scores
        assert fused_default[0][1] != fused_custom[0][1]


class TestNormalizeScores:
    """Tests for score normalization."""

    def test_normalize_minmax(self):
        """Test min-max normalization."""
        results = [("doc1", 0.0), ("doc2", 0.5), ("doc3", 1.0)]

        normalized = normalize_scores(results, method="minmax")

        assert normalized[0][1] == 0.0  # min -> 0
        assert normalized[1][1] == 0.5  # middle -> 0.5
        assert normalized[2][1] == 1.0  # max -> 1

    def test_normalize_rank(self):
        """Test rank-based normalization."""
        results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]

        normalized = normalize_scores(results, method="rank")

        # First should have highest score, last lowest
        assert normalized[0][1] > normalized[1][1]
        assert normalized[1][1] > normalized[2][1]

    def test_normalize_empty(self):
        """Test normalization with empty results."""
        assert normalize_scores([]) == []

    def test_normalize_single_value(self):
        """Test normalization when all scores are same."""
        results = [("doc1", 0.5), ("doc2", 0.5)]

        normalized = normalize_scores(results, method="minmax")

        # All values same -> all normalized to 1.0
        assert normalized[0][1] == 1.0
        assert normalized[1][1] == 1.0

    def test_normalize_preserves_order(self):
        """Test that normalization preserves document order."""
        results = [("doc1", 0.0), ("doc2", 0.5), ("doc3", 1.0)]

        normalized = normalize_scores(results)

        doc_ids = [doc_id for doc_id, _ in normalized]
        assert doc_ids == ["doc1", "doc2", "doc3"]


class TestDistanceToScore:
    """Tests for distance to score conversion."""

    def test_distance_zero(self):
        """Test distance 0 -> score 1.0."""
        assert distance_to_score(0.0) == pytest.approx(1.0)

    def test_distance_one(self):
        """Test distance 1 -> score 0.5."""
        assert distance_to_score(1.0) == pytest.approx(0.5)

    def test_distance_negative(self):
        """Test negative distance -> score 1.0."""
        assert distance_to_score(-0.5) == pytest.approx(1.0)

    def test_distance_none(self):
        """Test None distance -> score 0.0."""
        assert distance_to_score(None) == 0.0

    def test_distance_large(self):
        """Test large distance -> low score."""
        score = distance_to_score(100.0)
        assert score < 0.02  # 1/(1+100) = 0.0099

    def test_distance_monotonic(self):
        """Test that score decreases as distance increases."""
        scores = [distance_to_score(d) for d in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]]

        # Scores should be strictly decreasing
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i + 1]
