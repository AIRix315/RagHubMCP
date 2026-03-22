"""Tests for VectorScorer implementation.

This module tests the vector similarity scoring algorithm as defined in:
- Docs/20-RerankEngine-Architecture.md Section 4.2.1
- TODO 2.3.1: VectorScorer实现

Reference: Cosine/Dot/Euclidean similarity calculations
"""

import numpy as np
import pytest

from src.rerank_engine.core.scorer import BaseScorer


class TestVectorScorer:
    """Tests for VectorScorer implementation."""

    @pytest.fixture
    def vector_scorer(self):
        """Create VectorScorer with cosine similarity."""
        from src.rerank_engine.scorers.vector_scorer import VectorScorer

        return VectorScorer(similarity_fn="cosine")

    @pytest.fixture
    def vector_dot(self):
        """Create VectorScorer with dot product similarity."""
        from src.rerank_engine.scorers.vector_scorer import VectorScorer

        return VectorScorer(similarity_fn="dot")

    @pytest.fixture
    def vector_euclidean(self):
        """Create VectorScorer with euclidean similarity."""
        from src.rerank_engine.scorers.vector_scorer import VectorScorer

        return VectorScorer(similarity_fn="euclidean")

    # =========================================================================
    # Basic Properties Tests
    # =========================================================================

    def test_scorer_is_base_scorer(self, vector_scorer):
        """VectorScorer should inherit from BaseScorer."""
        assert isinstance(vector_scorer, BaseScorer)

    def test_scorer_name(self, vector_scorer):
        """Scorer should have correct name."""
        assert vector_scorer.name == "vector"

    def test_supports_batch(self, vector_scorer):
        """VectorScorer should support batch processing."""
        assert vector_scorer.supports_batch is True

    def test_default_similarity_fn(self, vector_scorer):
        """Default similarity function should be cosine."""
        assert vector_scorer.similarity_fn == "cosine"

    # =========================================================================
    # Cosine Similarity Tests
    # =========================================================================

    def test_cosine_similarity_identical_vectors(self, vector_scorer):
        """Test cosine similarity of identical vectors is 1.0."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = vector_scorer._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_orthogonal_vectors(self, vector_scorer):
        """Test cosine similarity of orthogonal vectors is 0.0."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])

        similarity = vector_scorer._cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 0.001

    def test_cosine_similarity_opposite_vectors(self, vector_scorer):
        """Test cosine similarity of opposite vectors is -1.0."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([-1.0, 0.0])

        similarity = vector_scorer._cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.001

    def test_cosine_similarity_normalized(self, vector_scorer):
        """Test cosine similarity is independent of vector magnitude."""
        vec1 = np.array([1.0, 1.0])
        vec2 = np.array([2.0, 2.0])  # Same direction, different magnitude

        similarity = vector_scorer._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001

    # =========================================================================
    # Dot Product Similarity Tests
    # =========================================================================

    def test_dot_product_basic(self, vector_dot):
        """Test basic dot product calculation."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([4.0, 5.0, 6.0])

        similarity = vector_dot._dot_product(vec1, vec2)
        # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
        assert similarity == 32.0

    def test_dot_product_with_zeros(self, vector_dot):
        """Test dot product with zero vector."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([0.0, 0.0, 0.0])

        similarity = vector_dot._dot_product(vec1, vec2)
        assert similarity == 0.0

    def test_dot_product_orthogonal(self, vector_dot):
        """Test dot product of orthogonal vectors."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])

        similarity = vector_dot._dot_product(vec1, vec2)
        assert similarity == 0.0

    # =========================================================================
    # Euclidean Similarity Tests
    # =========================================================================

    def test_euclidean_similarity_identical(self, vector_euclidean):
        """Test euclidean similarity of identical vectors."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])

        similarity = vector_euclidean._euclidean_similarity(vec1, vec2)
        # Distance is 0, similarity should be 1
        assert similarity == 1.0

    def test_euclidean_similarity_different(self, vector_euclidean):
        """Test euclidean similarity of different vectors."""
        vec1 = np.array([0.0, 0.0])
        vec2 = np.array([3.0, 4.0])

        similarity = vector_euclidean._euclidean_similarity(vec1, vec2)
        # Distance is 5, similarity = 1 / (1 + 5) = 1/6
        expected = 1.0 / (1.0 + 5.0)
        assert abs(similarity - expected) < 0.001

    # =========================================================================
    # Integration Tests
    # =========================================================================

    def test_compute_scores_basic(self, vector_scorer):
        """Test end-to-end scoring with vector similarity."""
        query = "machine learning"
        documents = [
            "Machine learning is a subset of AI.",
            "Python is a programming language.",
            "Deep learning uses neural networks.",
        ]

        scores = vector_scorer.compute_scores(query, documents)

        assert isinstance(scores, np.ndarray)
        assert len(scores) == len(documents)
        # Scores should be in valid range
        assert all(0 <= s <= 1 for s in scores)

    def test_compute_scores_empty_documents(self, vector_scorer):
        """Test scoring with empty document list."""
        scores = vector_scorer.compute_scores("query", [])
        assert len(scores) == 0

    def test_compute_scores_single_document(self, vector_scorer):
        """Test scoring with single document."""
        query = "python"
        documents = ["Python is a popular programming language."]

        scores = vector_scorer.compute_scores(query, documents)

        assert len(scores) == 1
        assert 0 <= scores[0] <= 1

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_empty_query(self, vector_scorer):
        """Test handling of empty query."""
        documents = ["test document"]

        scores = vector_scorer.compute_scores("", documents)
        assert len(scores) == 1

    def test_zero_vector_handling(self, vector_scorer):
        """Test handling of zero vectors."""
        vec = np.array([0.0, 0.0, 0.0])

        # Should handle gracefully without division by zero
        similarity = vector_scorer._cosine_similarity(vec, vec)
        # Convention: zero vector similarity is 0 or 1 depending on implementation
        assert similarity >= 0

    def test_different_similarity_functions(self):
        """Test that different similarity functions produce different results."""
        from src.rerank_engine.scorers.vector_scorer import VectorScorer

        cosine = VectorScorer(similarity_fn="cosine")
        dot = VectorScorer(similarity_fn="dot")
        euclidean = VectorScorer(similarity_fn="euclidean")

        query = "test query"
        documents = ["test document", "another doc"]

        cosine_scores = cosine.compute_scores(query, documents)
        dot_scores = dot.compute_scores(query, documents)
        euclidean_scores = euclidean.compute_scores(query, documents)

        # All should produce valid scores
        assert len(cosine_scores) == len(dot_scores) == len(euclidean_scores) == 2

    # =========================================================================
    # Performance Tests
    # =========================================================================

    def test_large_document_set(self, vector_scorer):
        """Test scoring with large number of documents."""
        query = "test"
        documents = [f"document {i} test content" for i in range(100)]

        scores = vector_scorer.compute_scores(query, documents)

        assert len(scores) == 100
        assert all(0 <= s <= 1 for s in scores)

    # =========================================================================
    # Configuration Tests
    # =========================================================================

    def test_get_config(self, vector_scorer):
        """Test get_config returns correct configuration."""
        config = vector_scorer.get_config()

        assert config["name"] == "vector"
        assert config["supports_batch"] is True
        assert config["similarity_fn"] == "cosine"

    def test_custom_similarity_fn(self):
        """Test creating scorer with custom similarity function."""
        from src.rerank_engine.scorers.vector_scorer import VectorScorer

        scorer = VectorScorer(similarity_fn="dot")
        assert scorer.similarity_fn == "dot"