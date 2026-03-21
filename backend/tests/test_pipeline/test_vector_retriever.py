"""Tests for VectorRetriever using ProviderFactory.

Reference: RULE.md (RULE-3: 禁止直接依赖具体实现)
"""

from unittest.mock import MagicMock, patch

import pytest

from pipeline.result import Document
from pipeline.retriever import VectorRetriever
from providers.vectorstore.base import QueryResult, SearchResult


class TestVectorRetrieverWithProvider:
    """Tests for VectorRetriever using ProviderFactory."""

    @pytest.mark.asyncio
    async def test_retrieve_uses_provider_factory(self):
        """Test retrieve uses ProviderFactory to get vectorstore."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(
            results=[
                SearchResult(id="1", document="doc1", metadata={}, score=0.1),
                SearchResult(id="2", document="doc2", metadata={}, score=0.2),
            ]
        )

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever(collection="test_collection")
            documents = await retriever.retrieve("test query")

            # Verify factory was called
            mock_factory.get_vectorstore_provider.assert_called_once()
            # Verify query was called with correct args
            mock_provider.query.assert_called_once()
            call_kwargs = mock_provider.query.call_args[1]
            assert call_kwargs["collection"] == "test_collection"
            assert call_kwargs["query_text"] == "test query"
            assert call_kwargs["n_results"] == 10

    @pytest.mark.asyncio
    async def test_retrieve_returns_documents(self):
        """Test retrieve returns properly formatted Document objects."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(
            results=[
                SearchResult(
                    id="doc-1", document="Document 1", metadata={"source": "file1.py"}, score=0.1
                ),
                SearchResult(
                    id="doc-2", document="Document 2", metadata={"source": "file2.py"}, score=0.2
                ),
            ]
        )

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")

            assert len(documents) == 2
            assert all(isinstance(doc, Document) for doc in documents)
            assert documents[0].id == "doc-1"
            assert documents[0].text == "Document 1"
            assert documents[1].id == "doc-2"

    @pytest.mark.asyncio
    async def test_retrieve_converts_distance_to_score(self):
        """Test retrieve converts ChromaDB distance to similarity score."""
        mock_provider = MagicMock()
        # ChromaDB returns distance (lower = better)
        mock_provider.query.return_value = QueryResult(
            results=[
                SearchResult(
                    id="1", document="Close match", metadata={}, score=0.0
                ),  # distance=0 means perfect match
                SearchResult(id="2", document="Far match", metadata={}, score=1.0),  # distance=1
            ]
        )

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")

            # Score should be 1.0/(1.0+distance) = 1.0 for distance=0
            assert documents[0].score == pytest.approx(1.0)
            # Score should be 1.0/(1.0+1.0) = 0.5 for distance=1
            assert documents[1].score == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_retrieve_passes_options(self):
        """Test retrieve passes options to vectorstore query."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(results=[])

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever()
            await retriever.retrieve(
                "test query",
                {"collection": "custom_collection", "topK": 15, "where": {"type": "pdf"}},
            )

            call_kwargs = mock_provider.query.call_args[1]
            assert call_kwargs["collection"] == "custom_collection"
            assert call_kwargs["n_results"] == 15
            assert call_kwargs["where"] == {"type": "pdf"}

    @pytest.mark.asyncio
    async def test_retrieve_uses_default_collection(self):
        """Test retrieve uses instance default collection when not specified."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(results=[])

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever(collection="my_default")
            await retriever.retrieve("test query")

            call_kwargs = mock_provider.query.call_args[1]
            assert call_kwargs["collection"] == "my_default"

    @pytest.mark.asyncio
    async def test_retrieve_handles_empty_results(self):
        """Test retrieve handles empty query results."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(results=[])

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")

            assert documents == []

    @pytest.mark.asyncio
    async def test_retrieve_handles_missing_metadata(self):
        """Test retrieve handles documents without metadata."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(
            results=[
                SearchResult(id="doc-1", document="Content", metadata=None, score=0.1),
            ]
        )

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")

            assert documents[0].metadata == {}

    @pytest.mark.asyncio
    async def test_retrieve_handles_missing_distances(self):
        """Test retrieve handles documents with None distance."""
        mock_provider = MagicMock()
        mock_provider.query.return_value = QueryResult(
            results=[
                SearchResult(id="doc-1", document="Content", metadata={}, score=None),
            ]
        )

        with patch("src.providers.factory.factory") as mock_factory:
            mock_factory.get_vectorstore_provider.return_value = mock_provider

            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")

            # Should default to score 0.0 when distance is None
            assert documents[0].score == 0.0
