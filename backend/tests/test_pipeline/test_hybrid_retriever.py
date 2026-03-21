"""Tests for HybridRetriever."""

from unittest.mock import MagicMock, patch

import pytest

from pipeline.retriever import HybridRetriever


class TestHybridRetriever:
    """Tests for HybridRetriever class."""

    def test_hybrid_retriever_initialization(self):
        """Test HybridRetriever initialization."""
        retriever = HybridRetriever(alpha=0.6, beta=0.4, rrf_k=50)

        assert retriever._alpha == 0.6
        assert retriever._beta == 0.4
        assert retriever._rrf_k == 50

    def test_hybrid_retriever_defaults(self):
        """Test HybridRetriever default values."""
        retriever = HybridRetriever()

        assert retriever._alpha == 0.5
        assert retriever._beta == 0.5
        assert retriever._rrf_k == 60

    def test_hybrid_retriever_properties(self):
        """Test HybridRetriever properties."""
        retriever = HybridRetriever(alpha=0.7, beta=0.3)

        assert retriever.alpha == 0.7
        assert retriever.beta == 0.3

    def test_hybrid_retriever_name_property(self):
        """Test name property returns class name."""
        retriever = HybridRetriever()

        assert retriever.name == "HybridRetriever"

    @pytest.mark.asyncio
    async def test_hybrid_retriever_retrieve(self):
        """Test HybridRetriever retrieve method."""
        # Mock the hybrid search service result
        mock_result = MagicMock()
        mock_result.id = "doc1"
        mock_result.text = "test document"
        mock_result.score = 0.95
        mock_result.metadata = {"source": "test.py"}
        mock_result.vector_score = 0.9
        mock_result.bm25_score = 0.8

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_result]

        with patch("src.services.hybrid_search.get_hybrid_search_service") as mock_get_service:
            mock_get_service.return_value = mock_service

            retriever = HybridRetriever(alpha=0.6, beta=0.4)
            documents = await retriever.retrieve("test query")

            assert len(documents) == 1
            assert documents[0].id == "doc1"
            assert documents[0].text == "test document"
            assert documents[0].score == 0.95
            assert documents[0].metadata == {"source": "test.py"}
            assert documents[0].vector_score == 0.9
            assert documents[0].bm25_score == 0.8

    @pytest.mark.asyncio
    async def test_hybrid_retriever_retrieve_with_options(self):
        """Test HybridRetriever with retrieval options."""
        mock_result = MagicMock()
        mock_result.id = "doc1"
        mock_result.text = "test"
        mock_result.score = 0.9
        mock_result.metadata = None
        mock_result.vector_score = 0.8
        mock_result.bm25_score = 0.7

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_result]

        with patch("src.services.hybrid_search.get_hybrid_search_service") as mock_get_service:
            mock_get_service.return_value = mock_service

            retriever = HybridRetriever()
            documents = await retriever.retrieve(
                "query", {"collection": "test_col", "topK": 5, "where": {"type": "pdf"}}
            )

            # Verify search was called with correct parameters
            mock_service.search.assert_called_once()
            call_kwargs = mock_service.search.call_args[1]
            assert call_kwargs["collection_name"] == "test_col"
            assert call_kwargs["n_results"] == 5
            assert call_kwargs["where"] == {"type": "pdf"}

    @pytest.mark.asyncio
    async def test_hybrid_retriever_handles_empty_results(self):
        """Test HybridRetriever handles empty results."""
        mock_service = MagicMock()
        mock_service.search.return_value = []

        with patch("src.services.hybrid_search.get_hybrid_search_service") as mock_get_service:
            mock_get_service.return_value = mock_service

            retriever = HybridRetriever()
            documents = await retriever.retrieve("test query")

            assert documents == []

    @pytest.mark.asyncio
    async def test_hybrid_retriever_handles_missing_metadata(self):
        """Test HybridRetriever handles missing metadata."""
        mock_result = MagicMock()
        mock_result.id = "doc1"
        mock_result.text = "test"
        mock_result.score = 0.9
        mock_result.metadata = None
        mock_result.vector_score = 0.8
        mock_result.bm25_score = 0.7

        mock_service = MagicMock()
        mock_service.search.return_value = [mock_result]

        with patch("src.services.hybrid_search.get_hybrid_search_service") as mock_get_service:
            mock_get_service.return_value = mock_service

            retriever = HybridRetriever()
            documents = await retriever.retrieve("test query")

            # Should handle None metadata
            assert documents[0].metadata == {}
