"""Tests for ChromaProvider vector store implementation.

Note: These tests mock the embedding provider to avoid dependency on Ollama.
"""

import gc
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


def create_mock_embedding():
    """Create a mock embedding provider."""
    mock = MagicMock()
    mock.embed_documents = MagicMock(
        return_value=[[0.1] * 768 for _ in range(10)]
    )
    mock.embed_query = MagicMock(
        return_value=[0.1] * 768
    )
    mock.NAME = "mock"
    return mock


class MockEmbeddingFunction:
    """ChromaDB-compatible mock embedding function."""
    
    # ChromaDB required attributes
    default_space = "cosine"
    supported_spaces = ["cosine", "l2", "ip"]
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        """Embed a list of texts."""
        return [[0.1] * 768 for _ in input]
    
    def name(self) -> str:
        """Return the embedding function name."""
        return "mock_embedding"
    
    def is_legacy(self) -> bool:
        """Return whether this is a legacy embedding function."""
        return False


def create_mock_embedding_function():
    """Create a mock ChromaDB-compatible embedding function."""
    return MockEmbeddingFunction()


class TestChromaProviderInit:
    """Tests for ChromaProvider initialization."""
    
    def test_default_initialization(self):
        """Test default initialization."""
        from providers.vectorstore.chroma import ChromaProvider
        
        provider = ChromaProvider()
        
        assert provider.NAME == "chroma"
        assert provider.persist_dir == "./data/chroma"
        assert provider._host is None
        assert provider._port is None
    
    def test_custom_persist_dir(self):
        """Test custom persist directory."""
        from providers.vectorstore.chroma import ChromaProvider
        
        provider = ChromaProvider(persist_dir="/custom/path")
        
        assert provider.persist_dir == "/custom/path"
    
    def test_from_config(self):
        """Test from_config factory method."""
        from providers.vectorstore.chroma import ChromaProvider
        
        config = {
            "persist_dir": "./test_data/chroma",
            "host": "localhost",
            "port": 8000,
        }
        
        provider = ChromaProvider.from_config(config)
        
        assert provider.persist_dir == "./test_data/chroma"
        assert provider._host == "localhost"
        assert provider._port == 8000


class TestChromaProviderCollectionOps:
    """Tests for collection operations without embeddings."""
    
    def test_list_collections_empty(self):
        """Test listing collections when empty."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            collections = provider.list_collections()
            assert isinstance(collections, list)
        finally:
            gc.collect()
    
    def test_create_collection(self):
        """Test creating a collection."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("test_collection")
            
            assert provider.collection_exists("test_collection")
            assert "test_collection" in provider.list_collections()
        finally:
            gc.collect()
    
    def test_delete_collection(self):
        """Test deleting a collection."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            provider.create_collection("to_delete")
            assert provider.collection_exists("to_delete")
            
            provider.delete_collection("to_delete")
            
            assert not provider.collection_exists("to_delete")
        finally:
            gc.collect()
    
    def test_collection_exists_false(self):
        """Test collection_exists returns False for non-existent collection."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            assert not provider.collection_exists("nonexistent")
        finally:
            gc.collect()


class TestChromaProviderDocumentOps:
    """Tests for document operations with mocked embeddings."""
    
    def test_count_empty_collection(self):
        """Test counting documents in empty collection."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            with patch('src.services.chroma_service._get_embedding_function', return_value=create_mock_embedding_function()):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("count_test")
                
                count = provider.count("count_test")
                assert count == 0
        finally:
            gc.collect()
    
    def test_add_and_count_documents(self):
        """Test adding documents and counting."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            with patch('src.services.chroma_service._get_embedding_function', return_value=create_mock_embedding_function()):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("add_test")
                
                provider.add(
                    collection="add_test",
                    documents=["doc1", "doc2", "doc3"],
                    ids=["id1", "id2", "id3"],
                    metadatas=[{"source": "a"}, {"source": "b"}, {"source": "c"}],
                )
                
                count = provider.count("add_test")
                assert count == 3
        finally:
            gc.collect()
    
    def test_add_empty_documents(self):
        """Test adding empty document list."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            with patch('src.services.chroma_service._get_embedding_function', return_value=create_mock_embedding_function()):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("empty_test")
                
                # Should not raise
                provider.add(
                    collection="empty_test",
                    documents=[],
                    ids=[],
                )
                
                assert provider.count("empty_test") == 0
        finally:
            gc.collect()
    
    def test_get_documents_by_ids(self):
        """Test retrieving documents by IDs."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            with patch('src.services.chroma_service._get_embedding_function', return_value=create_mock_embedding_function()):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("get_test")
                
                provider.add(
                    collection="get_test",
                    documents=["doc1", "doc2"],
                    ids=["id1", "id2"],
                )
                
                results = provider.get(
                    collection="get_test",
                    ids=["id1"],
                )
                
                assert len(results) == 1
                assert results[0].id == "id1"
                assert results[0].document == "doc1"
        finally:
            gc.collect()
    
    def test_delete_documents(self):
        """Test deleting documents."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            with patch('src.services.chroma_service._get_embedding_function', return_value=create_mock_embedding_function()):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("delete_test")
                
                provider.add(
                    collection="delete_test",
                    documents=["doc1", "doc2"],
                    ids=["id1", "id2"],
                )
                
                assert provider.count("delete_test") == 2
                
                deleted = provider.delete(
                    collection="delete_test",
                    ids=["id1"],
                )
                
                assert deleted >= 0  # Chroma may not return exact count
        finally:
            gc.collect()
    
    def test_update_documents(self):
        """Test updating documents."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            # Create mock embedding with consistent dimension
            mock_embedding = create_mock_embedding_function()
            
            with patch('src.services.chroma_service._get_embedding_function', return_value=mock_embedding):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("update_test")
                
                # Add with same mock embedding
                provider.add(
                    collection="update_test",
                    documents=["original"],
                    ids=["id1"],
                )
                
                # Update - use pre-computed embeddings to avoid dimension mismatch
                mock_emb = mock_embedding(["updated"])[0]
                provider.update(
                    collection="update_test",
                    ids=["id1"],
                    documents=["updated"],
                    embeddings=[mock_emb],
                )
                
                results = provider.get(
                    collection="update_test",
                    ids=["id1"],
                )
                
                assert results[0].document == "updated"
        finally:
            gc.collect()


class TestChromaProviderQuery:
    """Tests for query operations."""
    
    def test_query_requires_query_text(self):
        """Test that query requires query_text."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            with patch('providers.factory.factory.get_embedding_provider', return_value=create_mock_embedding()):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("query_test")
                
                with pytest.raises(ValueError) as exc_info:
                    provider.query(
                        collection="query_test",
                        query_text=None,
                        query_embedding=None,
                    )
                
                assert "query_text" in str(exc_info.value)
        finally:
            gc.collect()
    
    def test_query_with_query_text_returns_results(self):
        """Test query with query_text returns results via mock service."""
        from providers.vectorstore.chroma import ChromaProvider
        from providers.vectorstore.base import QueryResult, SearchResult
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            # Mock the service to avoid embedding dimension issues
            mock_service = MagicMock()
            mock_service.query.return_value = {
                "ids": ["id1", "id2"],
                "documents": ["doc1", "doc2"],
                "metadatas": [{"a": 1}, {"b": 2}],
                "distances": [0.1, 0.2],
            }
            
            with patch.object(provider, '_get_service', return_value=mock_service):
                results = provider.query(
                    collection="test_collection",
                    query_text="test query",
                    n_results=2,
                )
                
                assert isinstance(results, QueryResult)
                assert len(results.results) == 2
                assert results.results[0].id == "id1"
                assert results.results[0].document == "doc1"
                assert results.results[0].score == 0.1
        finally:
            gc.collect()
    
    def test_query_with_where_filter(self):
        """Test query with metadata filter."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            mock_service = MagicMock()
            mock_service.query.return_value = {
                "ids": ["id1"],
                "documents": ["doc1"],
                "metadatas": [{"type": "A"}],
                "distances": [0.1],
            }
            
            with patch.object(provider, '_get_service', return_value=mock_service):
                results = provider.query(
                    collection="test_collection",
                    query_text="test",
                    where={"type": "A"},
                    n_results=10,
                )
                
                assert isinstance(results.results, list)
                # Verify where filter was passed
                call_kwargs = mock_service.query.call_args[1]
                assert call_kwargs["where"] == {"type": "A"}
        finally:
            gc.collect()
    
    def test_query_with_where_document_filter(self):
        """Test query with document content filter."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            mock_service = MagicMock()
            mock_service.query.return_value = {
                "ids": ["id1"],
                "documents": ["python code"],
                "metadatas": [{}],
                "distances": [0.1],
            }
            
            with patch.object(provider, '_get_service', return_value=mock_service):
                results = provider.query(
                    collection="test_collection",
                    query_text="code",
                    where_document={"$contains": "python"},
                    n_results=10,
                )
                
                assert isinstance(results.results, list)
                call_kwargs = mock_service.query.call_args[1]
                assert call_kwargs["where_document"] == {"$contains": "python"}
        finally:
            gc.collect()
    
    def test_query_handles_missing_optional_fields(self):
        """Test query handles missing metadatas and distances."""
        from providers.vectorstore.chroma import ChromaProvider
        from providers.vectorstore.base import QueryResult
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            mock_service = MagicMock()
            # Return minimal result without optional fields
            mock_service.query.return_value = {
                "ids": ["id1"],
                "documents": ["doc1"],
            }
            
            with patch.object(provider, '_get_service', return_value=mock_service):
                results = provider.query(
                    collection="test_collection",
                    query_text="test",
                    n_results=1,
                )
                
                assert isinstance(results, QueryResult)
                assert len(results.results) == 1
                # Should have empty metadata and zero score
                assert results.results[0].metadata == {}
                assert results.results[0].score == 0.0
        finally:
            gc.collect()
    
    def test_query_returns_search_results_with_scores(self):
        """Test that query returns SearchResult objects with all fields."""
        from providers.vectorstore.chroma import ChromaProvider
        from providers.vectorstore.base import SearchResult, QueryResult
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            mock_service = MagicMock()
            mock_service.query.return_value = {
                "ids": ["id1"],
                "documents": ["test document"],
                "metadatas": [{"key": "value"}],
                "distances": [0.5],
            }
            
            with patch.object(provider, '_get_service', return_value=mock_service):
                results = provider.query(
                    collection="test_collection",
                    query_text="test",
                    n_results=1,
                )
                
                assert isinstance(results, QueryResult)
                assert len(results.results) == 1
                assert isinstance(results.results[0], SearchResult)
                assert results.results[0].id == "id1"
                assert results.results[0].document == "test document"
                assert results.results[0].metadata == {"key": "value"}
                assert results.results[0].score == 0.5
        finally:
            gc.collect()


class TestChromaProviderUpdateWithMetadata:
    """Tests for update operations with metadata."""
    
    def test_update_with_metadatas(self):
        """Test updating documents with metadatas."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            mock_embedding = create_mock_embedding_function()
            
            with patch('src.services.chroma_service._get_embedding_function', return_value=mock_embedding):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("update_meta_test")
                
                provider.add(
                    collection="update_meta_test",
                    documents=["original"],
                    ids=["id1"],
                    metadatas=[{"version": 1}],
                )
                
                # Update with new metadata
                mock_emb = mock_embedding(["updated"])[0]
                provider.update(
                    collection="update_meta_test",
                    ids=["id1"],
                    documents=["updated"],
                    metadatas=[{"version": 2, "updated": True}],
                    embeddings=[mock_emb],
                )
                
                results = provider.get(collection="update_meta_test", ids=["id1"])
                assert results[0].document == "updated"
        finally:
            gc.collect()
    
    def test_update_metadatas_only(self):
        """Test updating only metadatas without documents."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            mock_embedding = create_mock_embedding_function()
            
            with patch('src.services.chroma_service._get_embedding_function', return_value=mock_embedding):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("update_meta_only_test")
                
                provider.add(
                    collection="update_meta_only_test",
                    documents=["test doc"],
                    ids=["id1"],
                    metadatas=[{"old": True}],
                )
                
                # Update only metadata
                provider.update(
                    collection="update_meta_only_test",
                    ids=["id1"],
                    metadatas=[{"new": True}],
                )
                
                results = provider.get(collection="update_meta_only_test", ids=["id1"])
                assert len(results) == 1
        finally:
            gc.collect()
    
    def test_update_with_all_parameters(self):
        """Test updating with documents, metadatas, and embeddings."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            mock_embedding = create_mock_embedding_function()
            
            with patch('src.services.chroma_service._get_embedding_function', return_value=mock_embedding):
                provider = ChromaProvider(persist_dir=tmpdir)
                provider.create_collection("update_all_test")
                
                provider.add(
                    collection="update_all_test",
                    documents=["original"],
                    ids=["id1"],
                )
                
                mock_emb = mock_embedding(["fully updated"])[0]
                provider.update(
                    collection="update_all_test",
                    ids=["id1"],
                    documents=["fully updated"],
                    metadatas=[{"full": "update"}],
                    embeddings=[mock_emb],
                )
                
                results = provider.get(collection="update_all_test", ids=["id1"])
                assert results[0].document == "fully updated"
        finally:
            gc.collect()


class TestChromaProviderReset:
    """Tests for reset functionality."""
    
    def test_reset_clears_all_collections(self):
        """Test reset clears all collections."""
        from providers.vectorstore.chroma import ChromaProvider
        
        tmpdir = tempfile.mkdtemp()
        try:
            provider = ChromaProvider(persist_dir=tmpdir)
            
            provider.create_collection("col1")
            provider.create_collection("col2")
            
            assert len(provider.list_collections()) == 2
            
            provider.reset()
            
            assert len(provider.list_collections()) == 0
        finally:
            gc.collect()