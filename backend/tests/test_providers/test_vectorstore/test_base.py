"""Tests for VectorStore base classes and data structures."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        from providers.vectorstore.base import SearchResult

        result = SearchResult(
            id="doc1",
            document="Hello world",
            metadata={"source": "test"},
            score=0.95,
        )

        assert result.id == "doc1"
        assert result.document == "Hello world"
        assert result.metadata == {"source": "test"}
        assert result.score == 0.95

    def test_search_result_defaults(self):
        """Test SearchResult default values."""
        from providers.vectorstore.base import SearchResult

        result = SearchResult(id="doc1", document="test")

        assert result.metadata == {}
        assert result.score == 0.0


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_query_result_creation(self):
        """Test creating a QueryResult."""
        from providers.vectorstore.base import QueryResult, SearchResult

        results = [
            SearchResult(id="doc1", document="test1", score=0.9),
            SearchResult(id="doc2", document="test2", score=0.8),
        ]

        query_result = QueryResult(results=results, total=2)

        assert len(query_result.results) == 2
        assert query_result.total == 2

    def test_query_result_defaults(self):
        """Test QueryResult default values."""
        from providers.vectorstore.base import QueryResult

        result = QueryResult()

        assert result.results == []
        assert result.total is None


class TestBaseVectorStoreProvider:
    """Tests for BaseVectorStoreProvider abstract class."""

    def test_cannot_instantiate_abstract(self):
        """Cannot instantiate abstract class directly."""
        from providers.vectorstore.base import BaseVectorStoreProvider

        with pytest.raises(TypeError):
            BaseVectorStoreProvider()

    def test_subclass_must_implement_all_methods(self):
        """Subclass must implement all abstract methods."""
        from providers.vectorstore.base import BaseVectorStoreProvider

        class IncompleteProvider(BaseVectorStoreProvider):
            NAME = "incomplete"

            # Missing many method implementations

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_complete_implementation(self):
        """Complete implementation can be instantiated."""
        from providers.vectorstore.base import (
            BaseVectorStoreProvider,
            QueryResult,
        )

        class CompleteProvider(BaseVectorStoreProvider):
            NAME = "complete"

            def create_collection(self, name, metadata=None):
                pass

            def delete_collection(self, name):
                pass

            def list_collections(self):
                return []

            def collection_exists(self, name):
                return False

            def add(self, collection, documents, ids, metadatas=None, embeddings=None):
                pass

            def query(
                self,
                collection,
                query_text=None,
                query_embedding=None,
                n_results=10,
                where=None,
                where_document=None,
            ):
                return QueryResult()

            def get(self, collection, ids=None, where=None, limit=None, offset=None):
                return []

            def delete(self, collection, ids=None, where=None):
                return 0

            def count(self, collection):
                return 0

            def update(self, collection, ids, documents=None, metadatas=None, embeddings=None):
                pass

            @classmethod
            def from_config(cls, config):
                return cls()

        provider = CompleteProvider()
        assert provider.NAME == "complete"
