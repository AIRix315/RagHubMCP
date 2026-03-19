"""Tests for QdrantProvider vector store implementation."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


# Check if qdrant-client is available
try:
    import qdrant_client  # noqa: F401
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


@pytest.mark.skipif(not QDRANT_AVAILABLE, reason="qdrant-client not installed")
class TestQdrantProviderInit:
    """Tests for QdrantProvider initialization."""
    
    def test_default_initialization(self):
        """Test default initialization."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        provider = QdrantProvider()
        
        assert provider.NAME == "qdrant"
        assert provider._mode == "local"
        assert provider._embedding_dimension == 768
    
    def test_memory_mode(self):
        """Test memory mode initialization."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        provider = QdrantProvider(mode="memory")
        
        assert provider._mode == "memory"
    
    def test_custom_embedding_dimension(self):
        """Test custom embedding dimension."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        provider = QdrantProvider(
            mode="memory",
            embedding_dimension=1024,
        )
        
        assert provider._embedding_dimension == 1024
    
    def test_from_config_memory(self):
        """Test from_config factory method for memory mode."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        config = {
            "mode": "memory",
            "embedding_dimension": 512,
        }
        
        provider = QdrantProvider.from_config(config)
        
        assert provider._mode == "memory"
        assert provider._embedding_dimension == 512
    
    def test_from_config_local(self):
        """Test from_config factory method for local mode."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        config = {
            "mode": "local",
            "path": "./test_data/qdrant",
            "embedding_dimension": 768,
        }
        
        provider = QdrantProvider.from_config(config)
        
        assert provider._mode == "local"
        assert provider._path == "./test_data/qdrant"
    
    def test_from_config_remote(self):
        """Test from_config factory method for remote mode."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        config = {
            "mode": "remote",
            "host": "localhost",
            "port": 6333,
            "embedding_dimension": 1024,
        }
        
        provider = QdrantProvider.from_config(config)
        
        assert provider._mode == "remote"
        assert provider._host == "localhost"
        assert provider._port == 6333


@pytest.mark.skipif(not QDRANT_AVAILABLE, reason="qdrant-client not installed")
class TestQdrantProviderCollectionOps:
    """Tests for collection operations."""
    
    @pytest.fixture
    def memory_provider(self):
        """Create a provider with in-memory storage."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        provider = QdrantProvider(mode="memory", embedding_dimension=4)
        return provider
    
    def test_list_collections_empty(self, memory_provider):
        """Test listing collections when empty."""
        collections = memory_provider.list_collections()
        assert isinstance(collections, list)
    
    def test_create_collection(self, memory_provider):
        """Test creating a collection."""
        memory_provider.create_collection("test_collection")
        
        assert memory_provider.collection_exists("test_collection")
        assert "test_collection" in memory_provider.list_collections()
    
    def test_delete_collection(self, memory_provider):
        """Test deleting a collection."""
        memory_provider.create_collection("to_delete")
        assert memory_provider.collection_exists("to_delete")
        
        memory_provider.delete_collection("to_delete")
        
        assert not memory_provider.collection_exists("to_delete")
    
    def test_collection_exists_false(self, memory_provider):
        """Test collection_exists returns False for non-existent collection."""
        assert not memory_provider.collection_exists("nonexistent")


@pytest.mark.skipif(not QDRANT_AVAILABLE, reason="qdrant-client not installed")
class TestQdrantProviderDocumentOps:
    """Tests for document operations with mock embeddings."""
    
    @pytest.fixture
    def provider_with_mock_embedding(self):
        """Create a provider with mocked embedding provider."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        provider = QdrantProvider(mode="memory", embedding_dimension=4)
        
        # Mock embedding provider
        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        mock_embedding.embed_query = MagicMock(
            return_value=[0.1, 0.2, 0.3, 0.4]
        )
        provider._embedding_provider = mock_embedding
        
        return provider
    
    def test_count_empty_collection(self, provider_with_mock_embedding):
        """Test counting documents in empty collection."""
        provider_with_mock_embedding.create_collection("count_test")
        
        count = provider_with_mock_embedding.count("count_test")
        assert count == 0
    
    def test_add_documents_with_embeddings(self, provider_with_mock_embedding):
        """Test adding documents with pre-computed embeddings."""
        provider_with_mock_embedding.create_collection("add_test")
        
        embeddings = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
        ]
        
        provider_with_mock_embedding.add(
            collection="add_test",
            documents=["doc1", "doc2"],
            ids=["id1", "id2"],
            embeddings=embeddings,
        )
        
        assert provider_with_mock_embedding.count("add_test") == 2
    
    def test_add_documents_auto_embedding(self, provider_with_mock_embedding):
        """Test adding documents with auto-embedding."""
        provider_with_mock_embedding.create_collection("auto_embed_test")
        
        provider_with_mock_embedding.add(
            collection="auto_embed_test",
            documents=["doc1", "doc2"],
            ids=["id1", "id2"],
        )
        
        # Should have called embed_documents
        provider_with_mock_embedding._embedding_provider.embed_documents.assert_called()
        assert provider_with_mock_embedding.count("auto_embed_test") == 2
    
    def test_get_documents_by_ids(self, provider_with_mock_embedding):
        """Test retrieving documents by IDs."""
        provider_with_mock_embedding.create_collection("get_test")
        
        embeddings = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]
        
        provider_with_mock_embedding.add(
            collection="get_test",
            documents=["doc1", "doc2"],
            ids=["id1", "id2"],
            embeddings=embeddings,
        )
        
        results = provider_with_mock_embedding.get(
            collection="get_test",
            ids=["id1"],
        )
        
        assert len(results) == 1
        assert results[0].id == "id1"
        assert results[0].document == "doc1"
    
    def test_delete_documents_by_ids(self, provider_with_mock_embedding):
        """Test deleting documents by IDs."""
        provider_with_mock_embedding.create_collection("delete_test")
        
        embeddings = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]
        
        provider_with_mock_embedding.add(
            collection="delete_test",
            documents=["doc1", "doc2"],
            ids=["id1", "id2"],
            embeddings=embeddings,
        )
        
        assert provider_with_mock_embedding.count("delete_test") == 2
        
        deleted = provider_with_mock_embedding.delete(
            collection="delete_test",
            ids=["id1"],
        )
        
        assert deleted == 1


@pytest.mark.skipif(not QDRANT_AVAILABLE, reason="qdrant-client not installed")
class TestQdrantProviderQuery:
    """Tests for query operations."""
    
    @pytest.fixture
    def provider_with_data(self):
        """Create a provider with test data."""
        from providers.vectorstore.qdrant import QdrantProvider
        
        provider = QdrantProvider(mode="memory", embedding_dimension=4)
        
        # Mock embedding provider
        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        mock_embedding.embed_query = MagicMock(
            return_value=[0.1, 0.2, 0.3, 0.4]
        )
        provider._embedding_provider = mock_embedding
        
        provider.create_collection("query_test")
        
        embeddings = [
            [0.9, 0.1, 0.1, 0.1],
            [0.8, 0.2, 0.1, 0.1],
            [0.1, 0.1, 0.9, 0.1],
        ]
        
        provider.add(
            collection="query_test",
            documents=["Python is a programming language", "JavaScript is also a programming language", "The sky is blue"],
            ids=["p1", "p2", "p3"],
            embeddings=embeddings,
        )
        
        return provider
    
    def test_query_with_query_embedding(self, provider_with_data):
        """Test query with pre-computed embedding."""
        results = provider_with_data.query(
            collection="query_test",
            query_embedding=[0.9, 0.1, 0.1, 0.1],
            n_results=2,
        )
        
        assert len(results.results) == 2
        assert results.results[0].id in ["p1", "p2", "p3"]
    
    def test_query_with_query_text(self, provider_with_data):
        """Test query with text (auto-embedded)."""
        results = provider_with_data.query(
            collection="query_test",
            query_text="programming",
            n_results=2,
        )
        
        provider_with_data._embedding_provider.embed_query.assert_called()
        assert len(results.results) == 2
    
    def test_query_requires_query(self, provider_with_data):
        """Test that query requires either query_text or query_embedding."""
        with pytest.raises(ValueError) as exc_info:
            provider_with_data.query(
                collection="query_test",
                query_text=None,
                query_embedding=None,
            )
        
        assert "query_text" in str(exc_info.value) or "query_embedding" in str(exc_info.value)


class TestQdrantProviderWithoutClient:
    """Tests that don't require qdrant-client."""
    
    def test_qdrant_provider_name(self):
        """Test provider name is registered correctly."""
        from providers.base import ProviderCategory
        from providers.registry import registry
        
        # Check if qdrant is registered (it may not be if qdrant-client is not installed)
        if registry.is_registered(ProviderCategory.VECTORSTORE, "qdrant"):
            from providers.vectorstore.qdrant import QdrantProvider
            assert QdrantProvider.NAME == "qdrant"