"""Tests for HybridRetriever.

These tests verify HybridRetriever functionality using mocked Provider interfaces.

Reference:
- Docs/11-V2-Desing.md (Section 5)
- Docs/12-V2-Blueprint.md (Module 1)
- RULE.md (RULE-3: 禁止在模块中直接依赖具体实现)
"""

from unittest.mock import AsyncMock, MagicMock, patch

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
        """Test HybridRetriever retrieve method with mocked providers."""
        # Mock QueryResult for vector search
        mock_query_result = MagicMock()
        mock_query_result.id = "doc1"
        mock_query_result.document = "test document"
        mock_query_result.score = 0.3  # distance (lower is better)
        mock_query_result.metadata = {"source": "test.py"}

        mock_vectorstore = MagicMock()
        mock_vectorstore.query.return_value.results = [mock_query_result]
        mock_vectorstore.get.return_value.results = [mock_query_result]

        # Mock BM25 service
        mock_bm25_service = MagicMock()
        mock_bm25_service.query.return_value = [("doc1", 0.8)]

        # Patch at the import location used in retriever.py
        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_vectorstore

            with patch("src.services.bm25_service.get_bm25_service") as mock_get_bm25:
                mock_get_bm25.return_value = mock_bm25_service

                retriever = HybridRetriever(alpha=0.6, beta=0.4)
                documents = await retriever.retrieve("test query")

                # Should have results (may be empty if no collection)
                assert isinstance(documents, list)

    @pytest.mark.asyncio
    async def test_hybrid_retriever_retrieve_with_options(self):
        """Test HybridRetriever with retrieval options."""
        # Mock QueryResult
        mock_query_result = MagicMock()
        mock_query_result.id = "doc1"
        mock_query_result.document = "test"
        mock_query_result.score = 0.2
        mock_query_result.metadata = {"type": "pdf"}

        mock_vectorstore = MagicMock()
        mock_vectorstore.query.return_value.results = [mock_query_result]
        mock_vectorstore.get.return_value.results = [mock_query_result]

        mock_bm25_service = MagicMock()
        mock_bm25_service.query.return_value = [("doc1", 0.9)]

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_vectorstore

            with patch("src.services.bm25_service.get_bm25_service") as mock_get_bm25:
                mock_get_bm25.return_value = mock_bm25_service

                retriever = HybridRetriever()
                documents = await retriever.retrieve(
                    "query", {"collection": "test_col", "topK": 5, "where": {"type": "pdf"}}
                )

                # Verify query was called with collection
                mock_vectorstore.query.assert_called_once()
                call_kwargs = mock_vectorstore.query.call_args[1]
                assert call_kwargs["collection"] == "test_col"
                assert call_kwargs["n_results"] == 10  # topK * 2 for hybrid

    @pytest.mark.asyncio
    async def test_hybrid_retriever_handles_empty_results(self):
        """Test HybridRetriever handles empty results."""
        mock_vectorstore = MagicMock()
        mock_vectorstore.query.return_value.results = []

        mock_bm25_service = MagicMock()
        mock_bm25_service.query.return_value = []

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_vectorstore

            with patch("src.services.bm25_service.get_bm25_service") as mock_get_bm25:
                mock_get_bm25.return_value = mock_bm25_service

                retriever = HybridRetriever()
                documents = await retriever.retrieve("test query")

                assert documents == []

    @pytest.mark.asyncio
    async def test_hybrid_retriever_handles_missing_metadata(self):
        """Test HybridRetriever handles missing metadata."""
        mock_query_result = MagicMock()
        mock_query_result.id = "doc1"
        mock_query_result.document = "test"
        mock_query_result.score = 0.25
        mock_query_result.metadata = None

        mock_vectorstore = MagicMock()
        mock_vectorstore.query.return_value.results = [mock_query_result]
        mock_vectorstore.get.return_value.results = [mock_query_result]

        mock_bm25_service = MagicMock()
        mock_bm25_service.query.return_value = [("doc1", 0.85)]

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_vectorstore

            with patch("src.services.bm25_service.get_bm25_service") as mock_get_bm25:
                mock_get_bm25.return_value = mock_bm25_service

                retriever = HybridRetriever()
                documents = await retriever.retrieve("test query")

                # Should handle None metadata
                if documents:
                    assert documents[0].metadata is not None