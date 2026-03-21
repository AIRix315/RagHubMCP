"""Tests for QdrantProvider vector store implementation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


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
        mock_embedding.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
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
            ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
            embeddings=embeddings,
        )

        assert provider_with_mock_embedding.count("add_test") == 2

    def test_add_documents_auto_embedding(self, provider_with_mock_embedding):
        """Test adding documents with auto-embedding."""
        provider_with_mock_embedding.create_collection("auto_embed_test")

        provider_with_mock_embedding.add(
            collection="auto_embed_test",
            documents=["doc1", "doc2"],
            ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
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
            ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
            embeddings=embeddings,
        )

        results = provider_with_mock_embedding.get(
            collection="get_test",
            ids=["00000000-0000-0000-0000-000000000001"],
        )

        assert len(results) == 1
        assert results[0].id == "00000000-0000-0000-0000-000000000001"
        assert results[0].document == "doc1"

    def test_delete_documents_by_ids(self, provider_with_mock_embedding):
        """Test deleting documents by IDs."""
        provider_with_mock_embedding.create_collection("delete_test")

        embeddings = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]

        provider_with_mock_embedding.add(
            collection="delete_test",
            documents=["doc1", "doc2"],
            ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
            embeddings=embeddings,
        )

        assert provider_with_mock_embedding.count("delete_test") == 2

        deleted = provider_with_mock_embedding.delete(
            collection="delete_test",
            ids=["00000000-0000-0000-0000-000000000001"],
        )

        assert deleted == 1


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
        mock_embedding.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
        provider._embedding_provider = mock_embedding

        provider.create_collection("query_test")

        embeddings = [
            [0.9, 0.1, 0.1, 0.1],
            [0.8, 0.2, 0.1, 0.1],
            [0.1, 0.1, 0.9, 0.1],
        ]

        provider.add(
            collection="query_test",
            documents=[
                "Python is a programming language",
                "JavaScript is also a programming language",
                "The sky is blue",
            ],
            ids=[
                "00000000-0000-0000-0000-000000000011",
                "00000000-0000-0000-0000-000000000012",
                "00000000-0000-0000-0000-000000000013",
            ],
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
        assert results.results[0].id in [
            "00000000-0000-0000-0000-000000000011",
            "00000000-0000-0000-0000-000000000012",
            "00000000-0000-0000-0000-000000000013",
        ]

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


class TestQdrantProviderClientModes:
    """Tests for different client initialization modes."""

    def test_from_config_cloud_mode(self):
        """Test from_config for cloud mode."""
        from providers.vectorstore.qdrant import QdrantProvider

        config = {
            "mode": "cloud",
            "url": "https://test-cluster.cloud.qdrant.io:6333",
            "api_key": "test-api-key",
            "embedding_dimension": 768,
        }

        provider = QdrantProvider.from_config(config)

        assert provider._mode == "cloud"
        assert provider._url == "https://test-cluster.cloud.qdrant.io:6333"
        assert provider._api_key == "test-api-key"

    def test_from_config_with_grpc(self):
        """Test from_config with gRPC preference."""
        from providers.vectorstore.qdrant import QdrantProvider

        config = {
            "mode": "remote",
            "host": "localhost",
            "port": 6334,
            "prefer_grpc": True,
            "embedding_dimension": 768,
        }

        provider = QdrantProvider.from_config(config)

        assert provider._prefer_grpc is True

    def test_cloud_mode_initialization(self):
        """Test cloud mode initialization parameters."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(
            mode="cloud",
            url="https://test.cloud.qdrant.io:6333",
            api_key="test-key",
        )

        assert provider._mode == "cloud"
        assert provider._url == "https://test.cloud.qdrant.io:6333"
        assert provider._api_key == "test-key"

    def test_remote_mode_initialization(self):
        """Test remote mode initialization parameters."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(
            mode="remote",
            host="remote-host",
            port=6333,
        )

        assert provider._mode == "remote"
        assert provider._host == "remote-host"
        assert provider._port == 6333


class TestQdrantProviderFilterBuilding:
    """Tests for filter building methods."""

    @pytest.fixture
    def memory_provider(self):
        """Create a provider with in-memory storage."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(mode="memory", embedding_dimension=4)
        return provider

    def test_build_filter_exact_match(self, memory_provider):
        """Test _build_filter with exact match condition."""
        filter_dict = {"category": "books"}
        result = memory_provider._build_filter(filter_dict)

        # Should return a Filter object with must conditions
        assert result is not None

    def test_build_filter_range_gt(self, memory_provider):
        """Test _build_filter with greater than range."""
        filter_dict = {"price": {"$gt": 10}}
        result = memory_provider._build_filter(filter_dict)

        assert result is not None

    def test_build_filter_range_gte(self, memory_provider):
        """Test _build_filter with greater than or equal range."""
        filter_dict = {"price": {"$gte": 10}}
        result = memory_provider._build_filter(filter_dict)

        assert result is not None

    def test_build_filter_range_lt(self, memory_provider):
        """Test _build_filter with less than range."""
        filter_dict = {"price": {"$lt": 100}}
        result = memory_provider._build_filter(filter_dict)

        assert result is not None

    def test_build_filter_range_lte(self, memory_provider):
        """Test _build_filter with less than or equal range."""
        filter_dict = {"price": {"$lte": 100}}
        result = memory_provider._build_filter(filter_dict)

        assert result is not None

    def test_build_filter_contains(self, memory_provider):
        """Test _build_filter with contains condition."""
        filter_dict = {"content": {"$contains": "search term"}}
        result = memory_provider._build_filter(filter_dict)

        assert result is not None

    def test_build_filter_multiple_conditions(self, memory_provider):
        """Test _build_filter with multiple conditions."""
        filter_dict = {"category": "books", "year": {"$gt": 2020}}
        result = memory_provider._build_filter(filter_dict)

        assert result is not None

    def test_build_filter_empty_dict(self, memory_provider):
        """Test _build_filter with empty dict returns None."""
        result = memory_provider._build_filter({})

        assert result is None

    def test_build_document_filter_contains(self, memory_provider):
        """Test _build_document_filter with contains condition."""
        filter_dict = {"$contains": "search text"}
        result = memory_provider._build_document_filter(filter_dict)

        assert result is not None

    def test_build_document_filter_empty(self, memory_provider):
        """Test _build_document_filter without contains returns None."""
        filter_dict = {"$regex": "pattern"}
        result = memory_provider._build_document_filter(filter_dict)

        assert result is None


class TestQdrantProviderAddOperations:
    """Tests for add operations with edge cases."""

    @pytest.fixture
    def provider_with_mock_embedding(self):
        """Create a provider with mocked embedding provider."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(mode="memory", embedding_dimension=4)

        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        provider._embedding_provider = mock_embedding

        return provider

    def test_add_empty_documents_list(self, provider_with_mock_embedding):
        """Test adding empty documents list returns early."""
        result = provider_with_mock_embedding.add(
            collection="test",
            documents=[],
            ids=[],
        )

        # Should return None without error
        assert result is None

    def test_add_documents_with_metadatas(self, provider_with_mock_embedding):
        """Test adding documents with metadata."""
        provider_with_mock_embedding.create_collection("meta_test")

        embeddings = [[0.1, 0.2, 0.3, 0.4]]

        provider_with_mock_embedding.add(
            collection="meta_test",
            documents=["doc1"],
            ids=["00000000-0000-0000-0000-000000000001"],
            metadatas=[{"author": "test", "year": 2024}],
            embeddings=embeddings,
        )

        assert provider_with_mock_embedding.count("meta_test") == 1

    def test_add_documents_auto_create_collection(self, provider_with_mock_embedding):
        """Test that add creates collection if not exists."""
        # Don't create collection first

        embeddings = [[0.1, 0.2, 0.3, 0.4]]

        provider_with_mock_embedding.add(
            collection="auto_created",
            documents=["doc1"],
            ids=["00000000-0000-0000-0000-000000000001"],
            embeddings=embeddings,
        )

        # Collection should be created automatically
        assert provider_with_mock_embedding.collection_exists("auto_created")


class TestQdrantProviderGetOperations:
    """Tests for get operations with different parameters."""

    @pytest.fixture
    def provider_with_data(self):
        """Create a provider with test data."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(mode="memory", embedding_dimension=4)

        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        provider._embedding_provider = mock_embedding

        provider.create_collection("get_ops_test")

        embeddings = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 1.1, 1.2],
        ]

        provider.add(
            collection="get_ops_test",
            documents=["doc1", "doc2", "doc3"],
            ids=[
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002",
                "00000000-0000-0000-0000-000000000003",
            ],
            metadatas=[{"category": "A"}, {"category": "B"}, {"category": "A"}],
            embeddings=embeddings,
        )

        return provider

    def test_get_without_ids_uses_scroll(self, provider_with_data):
        """Test get without IDs uses scroll operation."""
        results = provider_with_data.get(
            collection="get_ops_test",
            limit=10,
        )

        assert len(results) == 3

    def test_get_with_limit_and_offset(self, provider_with_data):
        """Test get with limit and offset."""
        results = provider_with_data.get(
            collection="get_ops_test",
            limit=2,
            offset=0,
        )

        assert len(results) == 2

    def test_get_with_where_filter(self, provider_with_data):
        """Test get with metadata filter."""
        results = provider_with_data.get(
            collection="get_ops_test",
            where={"category": "A"},
            limit=10,
        )

        # Should filter results by category
        assert isinstance(results, list)


class TestQdrantProviderDeleteOperations:
    """Tests for delete operations with different parameters."""

    @pytest.fixture
    def provider_with_data(self):
        """Create a provider with test data."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(mode="memory", embedding_dimension=4)

        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        provider._embedding_provider = mock_embedding

        provider.create_collection("delete_ops_test")

        embeddings = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
            [0.9, 1.0, 1.1, 1.2],
        ]

        provider.add(
            collection="delete_ops_test",
            documents=["doc1", "doc2", "doc3"],
            ids=[
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002",
                "00000000-0000-0000-0000-000000000003",
            ],
            metadatas=[{"category": "A"}, {"category": "B"}, {"category": "A"}],
            embeddings=embeddings,
        )

        return provider

    def test_delete_with_where_filter(self, provider_with_data):
        """Test delete with metadata filter."""
        deleted = provider_with_data.delete(
            collection="delete_ops_test",
            where={"category": "B"},
        )

        assert isinstance(deleted, int)

    def test_delete_without_ids_or_where_returns_zero(self, provider_with_data):
        """Test delete without IDs or where returns 0."""
        deleted = provider_with_data.delete(
            collection="delete_ops_test",
        )

        assert deleted == 0


class TestQdrantProviderUpdateOperations:
    """Tests for update operations."""

    @pytest.fixture
    def provider_with_data(self):
        """Create a provider with test data."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(mode="memory", embedding_dimension=4)

        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        provider._embedding_provider = mock_embedding

        provider.create_collection("update_test")

        embeddings = [[0.1, 0.2, 0.3, 0.4]]

        provider.add(
            collection="update_test",
            documents=["original doc"],
            ids=["00000000-0000-0000-0000-000000000001"],
            metadatas=[{"version": 1}],
            embeddings=embeddings,
        )

        return provider

    def test_update_document_only(self, provider_with_data):
        """Test updating document text only."""
        provider_with_data.update(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
            documents=["updated doc"],
        )

        # Verify update was called without error
        results = provider_with_data.get(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
        )
        assert len(results) == 1

    def test_update_metadata_only(self, provider_with_data):
        """Test updating metadata with embeddings."""
        # Qdrant requires vector for PointStruct, so we provide embeddings
        new_embeddings = [[0.5, 0.6, 0.7, 0.8]]

        provider_with_data.update(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
            metadatas=[{"version": 2, "updated": True}],
            embeddings=new_embeddings,
        )

        results = provider_with_data.get(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
        )
        assert len(results) == 1

    def test_update_with_embeddings(self, provider_with_data):
        """Test updating with new embeddings."""
        new_embeddings = [[0.5, 0.6, 0.7, 0.8]]

        provider_with_data.update(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
            embeddings=new_embeddings,
        )

        # Should complete without error
        results = provider_with_data.get(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
        )
        assert len(results) == 1

    def test_update_document_auto_embed(self, provider_with_data):
        """Test updating document triggers auto-embedding."""
        provider_with_data.update(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001"],
            documents=["new doc text"],
        )

        # Auto-embedding should be called
        provider_with_data._embedding_provider.embed_documents.assert_called()

    def test_update_multiple_documents(self, provider_with_data):
        """Test updating multiple documents at once."""
        # First add another document
        embeddings = [[0.9, 1.0, 1.1, 1.2]]
        provider_with_data.add(
            collection="update_test",
            documents=["second doc"],
            ids=["00000000-0000-0000-0000-000000000002"],
            embeddings=embeddings,
        )

        provider_with_data.update(
            collection="update_test",
            ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
            documents=["updated1", "updated2"],
        )

        results = provider_with_data.get(collection="update_test", limit=10)
        assert len(results) == 2


class TestQdrantProviderQueryWithFilters:
    """Tests for query operations with filters."""

    @pytest.fixture
    def provider_with_data(self):
        """Create a provider with test data."""
        from providers.vectorstore.qdrant import QdrantProvider

        provider = QdrantProvider(mode="memory", embedding_dimension=4)

        mock_embedding = MagicMock()
        mock_embedding.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3, 0.4] for _ in range(10)]
        )
        mock_embedding.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
        provider._embedding_provider = mock_embedding

        provider.create_collection("filter_query_test")

        embeddings = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
        ]

        provider.add(
            collection="filter_query_test",
            documents=["doc1", "doc2"],
            ids=["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
            metadatas=[{"type": "A"}, {"type": "B"}],
            embeddings=embeddings,
        )

        return provider

    def test_query_with_where_filter(self, provider_with_data):
        """Test query with metadata filter."""
        results = provider_with_data.query(
            collection="filter_query_test",
            query_embedding=[0.1, 0.2, 0.3, 0.4],
            where={"type": "A"},
            n_results=10,
        )

        assert isinstance(results.results, list)

    def test_query_with_where_document_filter(self, provider_with_data):
        """Test query with document content filter."""
        results = provider_with_data.query(
            collection="filter_query_test",
            query_embedding=[0.1, 0.2, 0.3, 0.4],
            where_document={"$contains": "doc"},
            n_results=10,
        )

        assert isinstance(results.results, list)
