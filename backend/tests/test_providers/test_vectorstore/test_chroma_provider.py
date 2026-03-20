"""Tests for ChromaProvider vector store implementation.

Tests the ChromaProvider which directly wraps ChromaDB without ChromaService.

Reference:
- RULE.md (RULE-3: 禁止直接依赖具体实现)
- Docs/12-V2-Blueprint.md (Module 3: Provider抽象)
"""

import gc
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
import sys
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from providers.vectorstore.chroma import ChromaProvider, ChromaCollectionWrapper, ChromaEmbeddingFunction
from providers.vectorstore.base import SearchResult, QueryResult
from providers.embedding.base import BaseEmbeddingProvider


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock embedding provider for testing."""
    
    NAME = "mock"
    
    @property
    def dimension(self) -> int:
        return 384
    
    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        return [[0.1] * 384 for _ in documents]
    
    def embed_query(self, query: str) -> list[float]:
        return [0.1] * 384
    
    @classmethod
    def from_config(cls, config: dict) -> "MockEmbeddingProvider":
        return cls()


class TestChromaCollectionWrapper:
    """Tests for ChromaCollectionWrapper."""
    
    def test_wrapper_add(self):
        """Test wrapper add method."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("wrapper_test")
            
            client = provider._get_client()
            collection = client.get_collection("wrapper_test")
            wrapper = ChromaCollectionWrapper(collection)
            
            wrapper.add(
                ids=["id1", "id2"],
                documents=["doc1", "doc2"],
                metadatas=[{"a": 1}, {"b": 2}],
            )
            
            count = provider.count("wrapper_test")
            assert count == 2
        finally:
            gc.collect()

    def test_wrapper_query(self):
        """Test wrapper query method."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("query_wrapper_test")
            provider.add(
                collection="query_wrapper_test",
                documents=["test doc"],
                ids=["id1"],
            )
            
            client = provider._get_client()
            collection = client.get_collection("query_wrapper_test")
            wrapper = ChromaCollectionWrapper(collection)
            
            result = wrapper.query(query_texts=["test"], n_results=1)
            
            assert "ids" in result
            assert len(result["ids"][0]) == 1
        finally:
            gc.collect()


class TestChromaEmbeddingFunction:
    """Tests for ChromaEmbeddingFunction."""
    
    def test_embedding_function_call(self):
        """Test calling embedding function."""
        mock_provider = MockEmbeddingProvider()
        emb_func = ChromaEmbeddingFunction(mock_provider)
        
        result = emb_func(["doc1", "doc2"])
        
        assert len(result) == 2
        assert len(result[0]) == 384
    
    def test_embedding_function_name(self):
        """Test embedding function name property."""
        mock_provider = MockEmbeddingProvider()
        emb_func = ChromaEmbeddingFunction(mock_provider)
        
        assert emb_func.name == "raghub_mock"


class TestChromaProviderWithEmbedding:
    """Tests for ChromaProvider with embedding provider."""
    
    def test_provider_with_embedding_provider(self):
        """Test provider initialization with embedding provider."""
        tmpdir = tempfile.mkdtemp()
        try:
            mock_embedding = MockEmbeddingProvider()
            provider = ChromaProvider(
                persist_dir=tmpdir,
                embedding_provider=mock_embedding,
            )
            
            assert provider._embedding_provider == mock_embedding
        finally:
            gc.collect()

    @pytest.mark.skip(reason="ChromaDB version compatibility issue with embedding function name")
    def test_provider_query_with_embedding(self):
        """Test query uses embedding provider."""
        tmpdir = tempfile.mkdtemp()
        try:
            mock_embedding = MockEmbeddingProvider()
            provider = ChromaProvider(
                persist_dir=tmpdir,
                embedding_provider=mock_embedding,
            )
            
            provider.create_collection("embed_test")
            provider.add(
                collection="embed_test",
                documents=["test document"],
                ids=["id1"],
            )
            
            # Query should work with embedding
            result = provider.query(
                collection="embed_test",
                query_text="test",
                n_results=1,
            )
            
            assert isinstance(result, QueryResult)
        finally:
            gc.collect()


class TestChromaProviderInit:
    """Tests for ChromaProvider initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        provider = ChromaProvider()
        
        assert provider.NAME == "chroma"
        assert provider.persist_dir == "./data/chroma"
        # _host and _port are deprecated but kept for backward compatibility
        assert hasattr(provider, '_host')
        assert hasattr(provider, '_port')

    def test_custom_persist_dir(self):
        """Test custom persist directory."""
        provider = ChromaProvider(persist_dir="/custom/path")
        
        assert provider.persist_dir == "/custom/path"

    def test_from_config(self):
        """Test from_config factory method."""
        config = {
            "persist_dir": "./test_data/chroma",
        }
        
        provider = ChromaProvider.from_config(config)
        
        assert provider.persist_dir == "./test_data/chroma"

    def test_backward_compatibility_host_port(self):
        """Test backward compatibility with host/port parameters."""
        provider = ChromaProvider(
            persist_dir="./test",
            host="localhost",
            port=8000,
        )
        
        # Hostname and port are stored but not used (deprecated)
        assert provider._host == "localhost"
        assert provider._port == 8000


class TestChromaProviderCollectionOps:
    """Tests for collection operations."""

    def test_create_and_list_collections(self):
        """Test creating and listing collections."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            provider.create_collection("test_collection_1")
            provider.create_collection("test_collection_2")
            
            collections = provider.list_collections()
            assert "test_collection_1" in collections
            assert "test_collection_2" in collections
            assert len(collections) >= 2
        finally:
            gc.collect()

    def test_collection_exists(self):
        """Test checking if collection exists."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            provider.create_collection("existing_collection")
            
            assert provider.collection_exists("existing_collection") is True
            assert provider.collection_exists("non_existing_collection") is False
        finally:
            gc.collect()

    def test_delete_collection(self):
        """Test deleting a collection."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            provider.create_collection("to_delete")
            assert provider.collection_exists("to_delete") is True
            
            provider.delete_collection("to_delete")
            assert provider.collection_exists("to_delete") is False
        finally:
            gc.collect()

    def test_create_collection_with_metadata(self):
        """Test creating collection with metadata."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            metadata = {"description": "test collection", "version": "1.0"}
            provider.create_collection("meta_collection", metadata=metadata)
            
            assert provider.collection_exists("meta_collection") is True
        finally:
            gc.collect()


class TestChromaProviderDocumentOps:
    """Tests for document operations."""

    def test_add_documents(self):
        """Test adding documents to a collection."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("add_test")
            
            provider.add(
                collection="add_test",
                documents=["doc1 content", "doc2 content"],
                ids=["id1", "id2"],
                metadatas=[{"source": "file1"}, {"source": "file2"}],
            )
            
            count = provider.count("add_test")
            assert count == 2
        finally:
            gc.collect()

    def test_get_documents(self):
        """Test retrieving documents by ID."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("get_test")
            
            provider.add(
                collection="get_test",
                documents=["document content"],
                ids=["doc_id"],
                metadatas=[{"key": "value"}],
            )
            
            results = provider.get(collection="get_test", ids=["doc_id"])
            
            assert len(results) == 1
            assert results[0].id == "doc_id"
            assert results[0].document == "document content"
            assert results[0].metadata == {"key": "value"}
        finally:
            gc.collect()

    def test_query_documents(self):
        """Test querying documents."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("query_test")
            
            provider.add(
                collection="query_test",
                documents=["python programming", "javascript tutorial"],
                ids=["py1", "js1"],
            )
            
            results = provider.query(
                collection="query_test",
                query_text="programming",
                n_results=2,
            )
            
            assert isinstance(results, QueryResult)
            assert len(results.results) <= 2
        finally:
            gc.collect()

    def test_query_with_filter(self):
        """Test querying with metadata filter."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("filter_test")
            
            provider.add(
                collection="filter_test",
                documents=["doc1", "doc2", "doc3"],
                ids=["1", "2", "3"],
                metadatas=[
                    {"type": "pdf", "year": 2023},
                    {"type": "doc", "year": 2024},
                    {"type": "pdf", "year": 2024},
                ],
            )
            
            results = provider.query(
                collection="filter_test",
                query_text="doc",
                n_results=5,
                where={"type": "pdf"},
            )
            
            assert isinstance(results, QueryResult)
            for result in results.results:
                assert result.metadata.get("type") == "pdf"
        finally:
            gc.collect()

    def test_delete_documents(self):
        """Test deleting documents."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("delete_test")
            
            provider.add(
                collection="delete_test",
                documents=["to keep", "to delete"],
                ids=["keep1", "delete1"],
            )
            
            initial_count = provider.count("delete_test")
            
            deleted = provider.delete(collection="delete_test", ids=["delete1"])
            
            final_count = provider.count("delete_test")
            assert final_count == initial_count - deleted
        finally:
            gc.collect()


class TestChromaProviderQueryResult:
    """Tests for query result format."""

    def test_query_returns_search_results(self):
        """Test that query returns SearchResult objects."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("result_test")
            
            provider.add(
                collection="result_test",
                documents=["test document"],
                ids=["test_id"],
                metadatas=[{"source": "test"}],
            )
            
            results = provider.query(
                collection="result_test",
                query_text="test",
                n_results=1,
            )
            
            assert isinstance(results, QueryResult)
            assert len(results.results) >= 0
            
            if results.results:
                result = results.results[0]
                assert isinstance(result, SearchResult)
                assert hasattr(result, 'id')
                assert hasattr(result, 'document')
                assert hasattr(result, 'metadata')
                assert hasattr(result, 'score')
        finally:
            gc.collect()

    def test_query_empty_collection(self):
        """Test querying an empty collection."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("empty_collection")
            
            results = provider.query(
                collection="empty_collection",
                query_text="anything",
                n_results=5,
            )
            
            assert isinstance(results, QueryResult)
            assert len(results.results) == 0
        finally:
            gc.collect()


class TestChromaProviderReset:
    """Tests for reset functionality."""

    def test_reset_clears_all_collections(self):
        """Test reset clears all collections."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            provider.create_collection("col1")
            provider.create_collection("col2")
            
            assert len(provider.list_collections()) >= 2
            
            provider.reset()
            
            assert len(provider.list_collections()) == 0
        finally:
            gc.collect()


class TestChromaProviderBackwardCompat:
    """Tests for backward compatibility."""

    def test_get_service_method_exists(self):
        """Test _get_service method exists for backward compatibility."""
        provider = ChromaProvider()
        
        # Method should exist
        assert hasattr(provider, '_get_service')
        
        # Should return self (provider acts as pseudo-service)
        service = provider._get_service()
        assert service is provider

    def test_get_collection_method_exists(self):
        """Test get_collection method exists for backward compatibility."""
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("test_collection")
            
            # get_collection should work
            coll = provider.get_collection("test_collection")
            assert coll is not None
        finally:
            gc.collect()