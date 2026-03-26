"""BM25 Scorer tests."""

import pytest

from raghub_mcp.rerank_engine.scorers.bm25_scorer import BM25Scorer


class TestBM25Scorer:
    """Tests for BM25 scorer."""

    def test_bm25_scorer_basic(self):
        """Test basic BM25 scoring."""
        scorer = BM25Scorer()

        query = "machine learning"
        documents = [
            "Machine learning is a subset of AI",
            "Python is a programming language",
            "Deep learning uses neural networks",
        ]

        scores = scorer.compute_scores(query, documents)

        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)
        # ML document should score higher than unrelated ones
        assert scores[0] > scores[1]

    def test_bm25_scorer_empty_documents(self):
        """Test BM25 with empty documents."""
        scorer = BM25Scorer()
        scores = scorer.compute_scores("query", [])
        assert len(scores) == 0

    def test_bm25_scorer_name(self):
        """Test BM25 scorer name."""
        scorer = BM25Scorer()
        assert "bm25" in scorer.name.lower()

    def test_bm25_scorer_no_embedding_needed(self):
        """Test BM25 works without embedding provider."""
        scorer = BM25Scorer()
        # BM25 doesn't need embedding_provider
        scores = scorer.compute_scores("test", ["doc1", "doc2"])
        assert len(scores) == 2

    def test_bm25_scorer_empty_query(self):
        """Test BM25 with empty query."""
        scorer = BM25Scorer()
        scores = scorer.compute_scores("", ["doc1", "doc2"])
        assert len(scores) == 2
        # All scores should be zero for empty query
        assert all(s == 0 for s in scores)