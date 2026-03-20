"""Tests for pipeline retriever module.

These tests verify:
- Retriever abstract base class interface
- HybridRetriever implementation
- VectorRetriever implementation

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.retriever import Retriever, HybridRetriever, VectorRetriever
from pipeline.result import Document


class TestRetrieverABC:
    """Tests for Retriever abstract base class."""

    def test_retriever_is_abstract(self):
        """Test Retriever cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Retriever()

    def test_retriever_requires_retrieve_method(self):
        """Test Retriever subclass must implement retrieve method."""
        
        class IncompleteRetriever(Retriever):
            pass
        
        with pytest.raises(TypeError):
            IncompleteRetriever()

    def test_retriever_name_property(self):
        """Test retriever name property returns class name."""
        
        class TestRetriever(Retriever):
            async def retrieve(self, query: str, options: dict = None) -> list[Document]:
                return []
        
        retriever = TestRetriever()
        assert retriever.name == "TestRetriever"


class TestHybridRetriever:
    """Tests for HybridRetriever implementation."""

    def test_init_default_params(self):
        """Test HybridRetriever initializes with default parameters."""
        retriever = HybridRetriever()
        
        assert retriever.alpha == 0.5
        assert retriever.beta == 0.5

    def test_init_custom_params(self):
        """Test HybridRetriever initializes with custom parameters."""
        retriever = HybridRetriever(alpha=0.7, beta=0.3, rrf_k=100)
        
        assert retriever.alpha == 0.7
        assert retriever.beta == 0.3

    def test_name_property(self):
        """Test HybridRetriever name property."""
        retriever = HybridRetriever()
        assert retriever.name == "HybridRetriever"

    @pytest.mark.asyncio
    async def test_retrieve_returns_documents(self):
        """Test retrieve returns list of Document objects."""
        # Mock the hybrid search service
        mock_result = MagicMock()
        mock_result.id = "doc-1"
        mock_result.text = "Test document content"
        mock_result.score = 0.95
        mock_result.metadata = {"source": "test"}
        mock_result.vector_score = 0.92
        mock_result.bm25_score = 0.88
        
        mock_service = MagicMock()
        mock_service.search.return_value = [mock_result]
        
        with patch(
            "src.services.hybrid_search.get_hybrid_search_service",
            return_value=mock_service
        ):
            retriever = HybridRetriever()
            documents = await retriever.retrieve("test query")
            
            assert isinstance(documents, list)
            assert len(documents) == 1
            assert isinstance(documents[0], Document)
            assert documents[0].id == "doc-1"
            assert documents[0].text == "Test document content"
            assert documents[0].score == 0.95

    @pytest.mark.asyncio
    async def test_retrieve_passes_options(self):
        """Test retrieve passes options to service correctly."""
        mock_service = MagicMock()
        mock_service.search.return_value = []
        
        with patch(
            "src.services.hybrid_search.get_hybrid_search_service",
            return_value=mock_service
        ):
            retriever = HybridRetriever()
            await retriever.retrieve(
                "test query",
                {"collection": "test_collection", "topK": 20, "where": {"type": "doc"}}
            )
            
            mock_service.search.assert_called_once()
            call_kwargs = mock_service.search.call_args[1]
            assert call_kwargs["collection_name"] == "test_collection"
            assert call_kwargs["n_results"] == 20
            assert call_kwargs["where"] == {"type": "doc"}

    @pytest.mark.asyncio
    async def test_retrieve_default_options(self):
        """Test retrieve uses default options when not provided."""
        mock_service = MagicMock()
        mock_service.search.return_value = []
        
        with patch(
            "src.services.hybrid_search.get_hybrid_search_service",
            return_value=mock_service
        ):
            retriever = HybridRetriever()
            await retriever.retrieve("test query")
            
            call_kwargs = mock_service.search.call_args[1]
            assert call_kwargs["collection_name"] == "default"
            assert call_kwargs["n_results"] == 10

    @pytest.mark.asyncio
    async def test_retrieve_passes_alpha_beta_rrfk(self):
        """Test retrieve passes alpha, beta, rrf_k to service."""
        mock_service = MagicMock()
        mock_service.search.return_value = []
        
        with patch(
            "src.services.hybrid_search.get_hybrid_search_service"
        ) as mock_get_service:
            mock_get_service.return_value = mock_service
            
            retriever = HybridRetriever(alpha=0.7, beta=0.3, rrf_k=100)
            await retriever.retrieve("test query")
            
            mock_get_service.assert_called_once_with(
                alpha=0.7,
                beta=0.3,
                rrf_k=100,
            )


class TestVectorRetriever:
    """Tests for VectorRetriever implementation."""

    def test_init_default_collection(self):
        """Test VectorRetriever initializes with default collection."""
        retriever = VectorRetriever()
        # No direct way to verify, but should not raise

    def test_init_custom_collection(self):
        """Test VectorRetriever initializes with custom collection."""
        retriever = VectorRetriever(collection="my_collection")
        # Should not raise

    def test_name_property(self):
        """Test VectorRetriever name property."""
        retriever = VectorRetriever()
        assert retriever.name == "VectorRetriever"

    @pytest.mark.asyncio
    async def test_retrieve_returns_documents(self):
        """Test retrieve returns list of Document objects."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": ["doc-1", "doc-2"],
            "documents": ["Content 1", "Content 2"],
            "metadatas": [{"source": "a"}, {"source": "b"}],
            "distances": [0.1, 0.2],
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")
            
            assert isinstance(documents, list)
            assert len(documents) == 2
            assert all(isinstance(d, Document) for d in documents)
            assert documents[0].id == "doc-1"
            assert documents[0].text == "Content 1"

    @pytest.mark.asyncio
    async def test_retrieve_converts_distance_to_score(self):
        """Test retrieve converts distance to similarity score."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": ["doc-1"],
            "documents": ["Content"],
            "metadatas": [{}],
            "distances": [0.5],  # distance 0.5 -> score ~0.67
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")
            
            # Score should be 1/(1+distance) = 1/1.5 = 0.666...
            assert abs(documents[0].score - 0.666) < 0.01
            assert documents[0].vector_score == documents[0].score

    @pytest.mark.asyncio
    async def test_retrieve_handles_empty_results(self):
        """Test retrieve handles empty results gracefully."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")
            
            assert isinstance(documents, list)
            assert len(documents) == 0

    @pytest.mark.asyncio
    async def test_retrieve_passes_options(self):
        """Test retrieve passes options to service correctly."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever(collection="default_collection")
            await retriever.retrieve(
                "test query",
                {"collection": "custom_collection", "topK": 15, "where": {"type": "pdf"}}
            )
            
            mock_service.query.assert_called_once()
            call_kwargs = mock_service.query.call_args[1]
            assert call_kwargs["collection_name"] == "custom_collection"
            assert call_kwargs["n_results"] == 15
            assert call_kwargs["where"] == {"type": "pdf"}

    @pytest.mark.asyncio
    async def test_retrieve_uses_default_collection(self):
        """Test retrieve uses instance default collection when not specified."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever(collection="my_default")
            await retriever.retrieve("test query")  # No collection in options
            
            call_kwargs = mock_service.query.call_args[1]
            assert call_kwargs["collection_name"] == "my_default"

    @pytest.mark.asyncio
    async def test_retrieve_handles_missing_metadata(self):
        """Test retrieve handles documents without metadata."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": ["doc-1"],
            "documents": ["Content"],
            "metadatas": [],  # Empty metadatas list
            "distances": [0.1],
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")
            
            assert documents[0].metadata == {}

    @pytest.mark.asyncio
    async def test_retrieve_handles_missing_distances(self):
        """Test retrieve handles documents without distances."""
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "ids": ["doc-1"],
            "documents": ["Content"],
            "metadatas": [{}],
            "distances": [],  # Empty distances list
        }
        
        with patch(
            "src.services.chroma_service.get_chroma_service",
            return_value=mock_service
        ):
            retriever = VectorRetriever()
            documents = await retriever.retrieve("test query")
            
            # Should default to score 0.0 when no distance available
            assert documents[0].score == 0.0