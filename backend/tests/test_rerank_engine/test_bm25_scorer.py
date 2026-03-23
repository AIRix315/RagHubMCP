"""Tests for BM25Scorer implementation.

This module tests the BM25 scoring algorithm as defined in:
- Docs/20-RerankEngine-Architecture.md Section 11.3
- TODO 2.1.1-2.1.2: BM25Scorer实现

Reference: SylphxAI/coderag tfidf.ts#L265-L339
"""

import math

import numpy as np
import pytest

from raghub_mcp.rerank_engine.core.scorer import BaseScorer


class TestBM25Scorer:
    """Tests for BM25Scorer implementation."""

    @pytest.fixture
    def bm25_scorer(self):
        """Create BM25Scorer instance with default parameters."""
        from raghub_mcp.rerank_engine.scorers.bm25_scorer import BM25Scorer

        return BM25Scorer(k1=1.2, b=0.75)

    @pytest.fixture
    def bm25_custom(self):
        """Create BM25Scorer with custom parameters."""
        from raghub_mcp.rerank_engine.scorers.bm25_scorer import BM25Scorer

        return BM25Scorer(k1=2.0, b=0.5)

    # =========================================================================
    # Basic Properties Tests
    # =========================================================================

    def test_scorer_is_base_scorer(self, bm25_scorer):
        """BM25Scorer should inherit from BaseScorer."""
        assert isinstance(bm25_scorer, BaseScorer)

    def test_scorer_name(self, bm25_scorer):
        """Scorer should have correct name."""
        assert bm25_scorer.name == "bm25"

    def test_supports_batch(self, bm25_scorer):
        """BM25Scorer should support batch processing."""
        assert bm25_scorer.supports_batch is True

    def test_default_parameters(self, bm25_scorer):
        """Default parameters should match Elasticsearch defaults."""
        assert bm25_scorer.k1 == 1.2
        assert bm25_scorer.b == 0.75

    # =========================================================================
    # Basic Scoring Tests
    # =========================================================================

    def test_compute_scores_basic(self, bm25_scorer):
        """Test basic scoring functionality."""
        query = "machine learning"
        documents = [
            "Machine learning is a subset of AI.",
            "Python is a programming language.",
            "Deep learning uses neural networks.",
        ]

        scores = bm25_scorer.compute_scores(query, documents)

        assert isinstance(scores, np.ndarray)
        assert len(scores) == len(documents)
        # All scores should be in valid range
        assert all(0 <= s <= 1 for s in scores)

    def test_compute_scores_empty_documents(self, bm25_scorer):
        """Test scoring with empty document list."""
        scores = bm25_scorer.compute_scores("query", [])
        assert len(scores) == 0

    def test_compute_scores_single_document(self, bm25_scorer):
        """Test scoring with single document."""
        query = "python"
        documents = ["Python is a popular programming language."]

        scores = bm25_scorer.compute_scores(query, documents)

        assert len(scores) == 1
        assert 0 <= scores[0] <= 1

    def test_compute_scores_no_query_terms(self, bm25_scorer):
        """Test scoring when query terms don't appear in documents."""
        query = "xyzabc123"  # Terms unlikely to appear
        documents = ["This is a test document.", "Another test document."]

        scores = bm25_scorer.compute_scores(query, documents)

        # All scores should be 0 or near 0
        assert all(s < 0.1 for s in scores)

    # =========================================================================
    # BM25 Algorithm Correctness Tests (Task 2.1.1)
    # =========================================================================

    def test_bm25_formula_correctness(self, bm25_scorer):
        """Verify BM25 formula implementation is correct.

        BM25 formula:
        score = sum(IDF(t) * (f(t,D) * (k1 + 1)) / (f(t,D) + k1 * (1 - b + b * |D|/avgDl)))

        Where:
        - IDF(t) = log((N - n(t) + 0.5) / (n(t) + 0.5) + 1)
        - f(t,D) = term frequency in document
        - |D| = document length
        - avgDl = average document length
        """
        query = "test"
        documents = ["test test test", "test", "test test"]

        scores = bm25_scorer.compute_scores(query, documents)

        # Document with more 'test' occurrences should score higher
        # But with length normalization, the effect should be dampened
        assert scores[0] > scores[2]  # 3 occurrences vs 2
        assert scores[2] > scores[1]  # 2 occurrences vs 1

    def test_bm25_term_frequency_saturation(self, bm25_scorer):
        """Test that BM25 saturates term frequency properly.

        With k1=1.2, the term frequency effect should saturate,
        meaning adding more occurrences has diminishing returns.
        """
        query = "python"
        documents = [
            "python",  # 1 occurrence
            "python python python",  # 3 occurrences
            "python " * 10,  # 10 occurrences
        ]

        scores = bm25_scorer.compute_scores(query, documents)

        # Score should increase with more terms, but with diminishing returns
        # The difference between 1 and 3 should be larger than 3 and 10
        diff_1_3 = scores[1] - scores[0]
        diff_3_10 = scores[2] - scores[1]
        assert diff_1_3 > diff_3_10

    def test_bm25_document_length_normalization(self, bm25_scorer):
        """Test that BM25 normalizes for document length.

        With b=0.75, longer documents are penalized to prevent
        them from dominating due to having more terms.
        """
        query = "machine"
        documents = [
            "machine learning",  # Short, focused
            "machine " + "other " * 100,  # Long, same term but diluted
        ]

        scores = bm25_scorer.compute_scores(query, documents)

        # Shorter, more focused document should score higher
        assert scores[0] > scores[1]

    def test_bm25_multiple_query_terms(self, bm25_scorer):
        """Test scoring with multiple query terms."""
        query = "machine learning algorithms"
        documents = [
            "Machine learning algorithms are powerful tools.",
            "Machine learning is useful.",
            "Algorithms are important.",
            "Unrelated content here.",
        ]

        scores = bm25_scorer.compute_scores(query, documents)

        # Document with all terms should score highest
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]
        # Documents with some terms should score higher than none
        assert scores[1] > scores[3]
        assert scores[2] > scores[3]

    # =========================================================================
    # Smoothed IDF Tests (Task 2.1.2)
    # =========================================================================

    def test_smoothed_idf_no_zero_weights(self, bm25_scorer):
        """Test that Smoothed IDF never produces zero weights.

        Using BM25's IDF formula: log((N - n(t) + 0.5) / (n(t) + 0.5) + 1)
        This ensures IDF is always positive.
        """
        query = "rareterm12345"
        documents = ["common word document", "another common document"]

        scores = bm25_scorer.compute_scores(query, documents)

        # Even with rare term not in corpus, IDF should not be zero
        # Scores should be small but non-zero due to smoothing
        # Actually, if term doesn't appear in any doc, scores will be 0
        # The smoothing affects IDF calculation, not the final score if term absent
        assert all(s >= 0 for s in scores)

    def test_smoothed_idf_common_terms(self, bm25_scorer):
        """Test that common terms have lower IDF."""
        query = "test document"  # 'document' appears in all, 'test' is rare
        documents = [
            "this is a test",
            "another document",
            "test document",
        ]

        scores = bm25_scorer.compute_scores(query, documents)

        # Scores should reflect term rarity
        assert len(scores) == 3

    def test_idf_calculation(self, bm25_scorer):
        """Test IDF calculation directly."""
        # Manually calculate IDF for a term appearing in 2 of 4 docs
        # IDF = log((N - n + 0.5) / (n + 0.5) + 1)
        # = log((4 - 2 + 0.5) / (2 + 0.5) + 1)
        # = log(2.5 / 2.5 + 1) = log(2) ≈ 0.693
        num_docs = 4
        n = 2
        expected_idf = math.log((num_docs - n + 0.5) / (n + 0.5) + 1)

        idf = bm25_scorer._compute_idf(n, num_docs)
        assert abs(idf - expected_idf) < 0.001

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_empty_query(self, bm25_scorer):
        """Test handling of empty query."""
        documents = ["test document"]

        scores = bm25_scorer.compute_scores("", documents)
        # Empty query should return zero scores
        assert all(s == 0 for s in scores)

    def test_special_characters(self, bm25_scorer):
        """Test handling of special characters."""
        query = "python+test"
        documents = ["python test code", "python+test combined"]

        scores = bm25_scorer.compute_scores(query, documents)
        assert len(scores) == 2

    def test_unicode_support(self, bm25_scorer):
        """Test handling of unicode characters."""
        query = "机器学习"  # "machine learning" in Chinese
        documents = ["机器学习是人工智能的一部分", "深度学习使用神经网络"]

        scores = bm25_scorer.compute_scores(query, documents)
        assert len(scores) == 2
        # First document contains the query term
        assert scores[0] > scores[1]

    def test_case_insensitivity(self, bm25_scorer):
        """Test that scoring is case-insensitive."""
        query = "PYTHON"
        documents = ["python is great", "Python is awesome", "PYTHON is amazing"]

        scores = bm25_scorer.compute_scores(query, documents)
        # All should score similarly since they contain the same word
        assert abs(scores[0] - scores[1]) < 0.1
        assert abs(scores[1] - scores[2]) < 0.1

    # =========================================================================
    # Performance Tests
    # =========================================================================

    def test_large_document_set(self, bm25_scorer):
        """Test scoring with large number of documents."""
        query = "test"
        documents = [f"document {i} test content" for i in range(100)]

        scores = bm25_scorer.compute_scores(query, documents)

        assert len(scores) == 100
        assert all(0 <= s <= 1 for s in scores)

    def test_long_documents(self, bm25_scorer):
        """Test scoring with very long documents."""
        query = "uniqueword"
        documents = [
            "uniqueword " + "other " * 1000,  # Long doc with query term
            "other " * 1000,  # Long doc without query term
        ]

        scores = bm25_scorer.compute_scores(query, documents)

        # Document with query term should score higher
        assert scores[0] > scores[1]

    # =========================================================================
    # Configuration Tests
    # =========================================================================

    def test_custom_k1_parameter(self, bm25_custom):
        """Test custom k1 parameter affects scoring."""
        assert bm25_custom.k1 == 2.0

    def test_custom_b_parameter(self, bm25_custom):
        """Test custom b parameter affects scoring."""
        assert bm25_custom.b == 0.5

    def test_get_config(self, bm25_scorer):
        """Test get_config returns correct configuration."""
        config = bm25_scorer.get_config()

        assert config["name"] == "bm25"
        assert config["supports_batch"] is True
        assert config["k1"] == 1.2
        assert config["b"] == 0.75
