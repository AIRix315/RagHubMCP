"""Tests for vector store migration utilities."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from utils.migrate import (
    CollectionMigrationResult,
    MigrationResult,
    VectorStoreMigrator,
    migrate_chroma_to_qdrant,
)


class TestMigrationResult:
    """Tests for MigrationResult dataclass."""

    def test_default_values(self) -> None:
        """Test default initialization."""
        result = MigrationResult()

        assert result.success is True
        assert result.collections_migrated == 0
        assert result.documents_migrated == 0
        assert result.collections == []
        assert result.errors == []
        assert result.warnings == []
        assert result.duration_seconds == 0.0

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        result = MigrationResult(
            success=True,
            collections_migrated=2,
            documents_migrated=100,
            collections=[
                {"name": "docs", "documents_migrated": 50, "success": True, "error": None},
            ],
            errors=["test error"],
            warnings=["test warning"],
            duration_seconds=1.5,
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["collections_migrated"] == 2
        assert d["documents_migrated"] == 100
        assert len(d["collections"]) == 1
        assert d["errors"] == ["test error"]
        assert d["warnings"] == ["test warning"]
        assert d["duration_seconds"] == 1.5


class TestCollectionMigrationResult:
    """Tests for CollectionMigrationResult dataclass."""

    def test_default_values(self) -> None:
        """Test default initialization."""
        result = CollectionMigrationResult(name="test_collection")

        assert result.name == "test_collection"
        assert result.documents_migrated == 0
        assert result.success is True
        assert result.error is None

    def test_to_dict(self) -> None:
        """Test serialization."""
        result = CollectionMigrationResult(
            name="test_collection",
            documents_migrated=50,
            success=False,
            error="Test error",
        )

        d = result.to_dict()

        assert d["name"] == "test_collection"
        assert d["documents_migrated"] == 50
        assert d["success"] is False
        assert d["error"] == "Test error"


class MockVectorStoreProvider:
    """Mock vector store provider for testing."""

    def __init__(
        self,
        collections: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        """Initialize mock provider.

        Args:
            collections: Dict mapping collection name to list of documents.
                        Each document is a dict with id, document, metadata, embedding.
        """
        self._collections = collections or {}
        self._name = "mock"

    @property
    def NAME(self) -> str:  # noqa: N802
        return self._name

    def list_collections(self) -> list[str]:
        return list(self._collections.keys())

    def collection_exists(self, name: str) -> bool:
        return name in self._collections

    def count(self, collection: str) -> int:
        if collection not in self._collections:
            return 0
        return len(self._collections[collection])

    def create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if name not in self._collections:
            self._collections[name] = []

    def delete_collection(self, name: str) -> None:
        self._collections.pop(name, None)

    def get(
        self,
        collection: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Any]:
        """Get documents from collection."""
        from providers.vectorstore import SearchResult

        if collection not in self._collections:
            return []

        docs = self._collections[collection]

        # Apply offset and limit
        if offset:
            docs = docs[offset:]
        if limit:
            docs = docs[:limit]

        return [
            SearchResult(
                id=doc["id"],
                document=doc.get("document", ""),
                metadata=doc.get("metadata", {}),
            )
            for doc in docs
        ]

    def add(
        self,
        collection: str,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        """Add documents to collection."""
        if collection not in self._collections:
            self._collections[collection] = []

        for i, doc_id in enumerate(ids):
            doc = {
                "id": doc_id,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "embedding": embeddings[i]
                if embeddings and i < len(embeddings)
                else [0.1, 0.2, 0.3],
            }
            self._collections[collection].append(doc)

    def _get_service(self) -> Any:
        """Mock method for Chroma compatibility."""
        return self

    def get_collection(self, name: str) -> Any:
        """Mock collection getter."""
        return MockChromaCollection(self._collections.get(name, []))


class MockChromaCollection:
    """Mock Chroma collection for testing."""

    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    def get(
        self,
        limit: int | None = None,
        offset: int | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get documents from collection."""
        docs = self._documents

        if offset:
            docs = docs[offset:]
        if limit:
            docs = docs[:limit]

        result = {
            "ids": [d["id"] for d in docs],
            "documents": [d.get("document", "") for d in docs],
            "metadatas": [d.get("metadata", {}) for d in docs],
        }

        if include and "embeddings" in include:
            result["embeddings"] = [d.get("embedding", [0.1, 0.2, 0.3]) for d in docs]

        return result


class TestVectorStoreMigrator:
    """Tests for VectorStoreMigrator."""

    def test_migrate_empty_source(self) -> None:
        """Test migration with no collections."""
        source = MockVectorStoreProvider()
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate()

        assert result.success is True
        assert result.collections_migrated == 0
        assert result.documents_migrated == 0
        assert "No collections found to migrate" in result.warnings

    def test_migrate_single_collection(self) -> None:
        """Test migrating a single collection."""
        source = MockVectorStoreProvider(
            {
                "test_docs": [
                    {
                        "id": "doc1",
                        "document": "Hello world",
                        "metadata": {"source": "test"},
                        "embedding": [0.1, 0.2, 0.3],
                    },
                    {
                        "id": "doc2",
                        "document": "Foo bar",
                        "metadata": {"source": "test"},
                        "embedding": [0.4, 0.5, 0.6],
                    },
                ],
            }
        )
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(verify=False)

        assert result.success is True
        assert result.collections_migrated == 1
        assert result.documents_migrated == 2

        # Verify target has the documents
        assert target.count("test_docs") == 2

    def test_migrate_multiple_collections(self) -> None:
        """Test migrating multiple collections."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1, 0.2]},
                ],
                "code": [
                    {"id": "c1", "document": "Code 1", "metadata": {}, "embedding": [0.3, 0.4]},
                    {"id": "c2", "document": "Code 2", "metadata": {}, "embedding": [0.5, 0.6]},
                ],
            }
        )
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(verify=False)

        assert result.success is True
        assert result.collections_migrated == 2
        assert result.documents_migrated == 3
        assert target.count("docs") == 1
        assert target.count("code") == 2

    def test_migrate_specific_collections(self) -> None:
        """Test migrating only specified collections."""
        source = MockVectorStoreProvider(
            {
                "docs": [{"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]}],
                "code": [{"id": "c1", "document": "Code 1", "metadata": {}, "embedding": [0.2]}],
                "test": [{"id": "t1", "document": "Test 1", "metadata": {}, "embedding": [0.3]}],
            }
        )
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(collections=["docs", "code"], verify=False)

        assert result.success is True
        assert result.collections_migrated == 2
        assert result.documents_migrated == 2
        assert target.collection_exists("docs")
        assert target.collection_exists("code")
        assert not target.collection_exists("test")

    def test_migrate_with_progress_callback(self) -> None:
        """Test migration with progress callback."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": f"d{i}", "document": f"Doc {i}", "metadata": {}, "embedding": [0.1]}
                    for i in range(5)
                ],
            }
        )
        target = MockVectorStoreProvider()

        progress_calls = []

        def progress_callback(current: int, total: int, message: str) -> None:
            progress_calls.append((current, total, message))

        migrator = VectorStoreMigrator(source, target, batch_size=2)
        result = migrator.migrate(progress_callback=progress_callback, verify=False)

        assert result.success is True
        assert len(progress_calls) > 0

    def test_migrate_with_verification(self) -> None:
        """Test migration with integrity verification."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                ],
            }
        )
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(verify=True)

        assert result.success is True
        assert result.collections_migrated == 1

    def test_migrate_empty_collection(self) -> None:
        """Test migrating an empty collection."""
        source = MockVectorStoreProvider(
            {
                "empty": [],
            }
        )
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(verify=False)

        assert result.success is True
        assert result.collections_migrated == 1
        assert result.documents_migrated == 0


class TestMigrateChromaToQdrant:
    """Tests for the convenience function."""

    @patch("providers.vectorstore.ChromaProvider")
    @patch("providers.vectorstore.QdrantProvider")
    def test_migrate_chroma_to_qdrant(
        self,
        mock_qdrant_class: MagicMock,
        mock_chroma_class: MagicMock,
    ) -> None:
        """Test the convenience function creates providers and calls migrate."""
        # Setup mocks
        mock_source = MagicMock()
        mock_source.list_collections.return_value = ["docs"]
        mock_source.collection_exists.return_value = True
        mock_source.count.return_value = 0
        mock_source._get_service.return_value.get_collection.return_value.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "embeddings": [],
        }

        mock_target = MagicMock()
        mock_target.list_collections.return_value = []
        mock_target.collection_exists.return_value = False
        mock_target.count.return_value = 0

        mock_chroma_class.return_value = mock_source
        mock_qdrant_class.return_value = mock_target

        # Execute
        result = migrate_chroma_to_qdrant(
            chroma_persist_dir="./test/chroma",
            qdrant_mode="memory",
            verify=False,
        )

        # Verify
        mock_chroma_class.assert_called_once_with(persist_dir="./test/chroma")
        mock_qdrant_class.assert_called_once()
        assert isinstance(result, MigrationResult)


class TestMigrationIntegration:
    """Integration tests for migration."""

    def test_full_migration_workflow(self, tmp_path: Any) -> None:
        """Test complete migration workflow with mock providers."""
        # Create source with data
        source = MockVectorStoreProvider(
            {
                "documentation": [
                    {
                        "id": f"doc_{i}",
                        "document": f"Document {i} content about testing",
                        "metadata": {"category": "test", "index": i},
                        "embedding": [0.1 * i, 0.2 * i, 0.3 * i],
                    }
                    for i in range(10)
                ],
                "code": [
                    {
                        "id": f"code_{i}",
                        "document": f"def function_{i}(): pass",
                        "metadata": {"language": "python"},
                        "embedding": [0.5, 0.6, 0.7],
                    }
                    for i in range(5)
                ],
            }
        )

        # Create empty target
        target = MockVectorStoreProvider()

        # Run migration
        migrator = VectorStoreMigrator(source, target, batch_size=5)
        result = migrator.migrate(verify=True)

        # Verify results
        assert result.success is True
        assert result.collections_migrated == 2
        assert result.documents_migrated == 15
        assert len(result.errors) == 0

        # Verify target state
        assert target.collection_exists("documentation")
        assert target.collection_exists("code")
        assert target.count("documentation") == 10
        assert target.count("code") == 5

    def test_migration_handles_missing_source_collection(self) -> None:
        """Test migration when source collection doesn't exist."""
        source = MockVectorStoreProvider({"existing": []})
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(collections=["nonexistent"], verify=False)

        # Should handle gracefully
        assert result.success is False  # Collection doesn't exist
        assert len(result.errors) > 0


class TestMigrateErrorPaths:
    """Tests for error paths and edge cases to improve coverage."""

    def test_migrate_list_collections_exception(self) -> None:
        """Test migration when list_collections raises an exception (lines 160-164)."""
        source = MagicMock()
        source.list_collections.side_effect = RuntimeError("Connection failed")
        target = MagicMock()

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(collections=None)  # Will trigger list_collections

        assert result.success is False
        assert len(result.errors) == 1
        assert "Failed to list source collections" in result.errors[0]
        assert result.duration_seconds > 0

    def test_migrate_with_verify_progress_callback(self) -> None:
        """Test migration with verify=True and progress callback (line 198)."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                ],
            }
        )
        target = MockVectorStoreProvider()

        progress_calls = []

        def progress_callback(current: int, total: int, message: str) -> None:
            progress_calls.append((current, total, message))

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(progress_callback=progress_callback, verify=True)

        assert result.success is True
        # Check that verification progress was called
        verify_calls = [c for c in progress_calls if "Verifying" in c[2]]
        assert len(verify_calls) > 0

    def test_migrate_verification_with_errors_and_warnings(self) -> None:
        """Test migration when verification returns errors and warnings (lines 205-206)."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                ],
            }
        )
        target = MockVectorStoreProvider()

        # Mock _verify_integrity to return errors/warnings
        migrator = VectorStoreMigrator(source, target)

        with patch.object(
            migrator,
            "_verify_integrity",
            return_value={
                "success": False,
                "errors": ["Count mismatch for 'docs': source=1, target=0"],
                "warnings": ["Could not verify embeddings"],
            },
        ):
            result = migrator.migrate(verify=True)

        assert result.success is False  # Has errors
        assert "Count mismatch" in result.errors[-1]
        assert "Could not verify embeddings" in result.warnings

    def test_migrate_batch_empty_ids(self) -> None:
        """Test migration when batch returns empty IDs (line 262)."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                ],
            }
        )
        target = MockVectorStoreProvider()

        migrator = VectorStoreMigrator(source, target)

        # Mock _read_batch to return empty IDs on first call
        with patch.object(
            migrator,
            "_read_batch",
            return_value={"ids": [], "documents": [], "metadatas": [], "embeddings": []},
        ):
            result = migrator.migrate(verify=False)

        assert result.success is True
        assert result.documents_migrated == 0  # No documents migrated due to empty batch

    def test_migrate_collection_exception(self) -> None:
        """Test migration when collection migration raises an exception (lines 284-287)."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                ],
            }
        )
        target = MagicMock()
        target.collection_exists.return_value = False
        target.create_collection.side_effect = RuntimeError("Failed to create collection")

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(verify=False)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Failed to create collection" in result.errors[0]

    def test_read_chroma_batch_success(self) -> None:
        """Test _read_chroma_batch method (lines 309, 343-359)."""
        source = MagicMock()
        source.NAME = "chroma"

        # Mock the Chroma service chain
        mock_service = MagicMock()
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [{"key": "val1"}, {"key": "val2"}],
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
        }
        mock_service.get_collection.return_value = mock_collection
        source._get_service.return_value = mock_service

        target = MagicMock()

        migrator = VectorStoreMigrator(source, target)
        result = migrator._read_chroma_batch("test_collection", 0, 10)

        assert result["ids"] == ["id1", "id2"]
        assert result["documents"] == ["doc1", "doc2"]
        assert result["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]
        mock_collection.get.assert_called_once_with(
            limit=10, offset=0, include=["documents", "metadatas", "embeddings"]
        )

    def test_read_chroma_batch_no_get_service(self) -> None:
        """Test _read_chroma_batch when source lacks _get_service (lines 343-345)."""
        source = MagicMock()
        source.NAME = "chroma"
        # Remove _get_service attribute
        delattr(source, "_get_service")

        target = MagicMock()

        migrator = VectorStoreMigrator(source, target)

        with pytest.raises(RuntimeError, match="Source provider does not support _get_service"):
            migrator._read_chroma_batch("test_collection", 0, 10)

    def test_read_chroma_batch_no_get_collection(self) -> None:
        """Test _read_chroma_batch when service lacks get_collection (lines 347-349)."""
        source = MagicMock()
        source.NAME = "chroma"

        # Mock service without get_collection
        mock_service = MagicMock()
        delattr(mock_service, "get_collection")
        source._get_service.return_value = mock_service

        target = MagicMock()

        migrator = VectorStoreMigrator(source, target)

        with pytest.raises(RuntimeError, match="Service does not support get_collection"):
            migrator._read_chroma_batch("test_collection", 0, 10)

    def test_read_batch_non_chroma_provider(self) -> None:
        """Test _read_batch with non-Chroma provider (lines 310-323)."""
        source = MagicMock()
        source.NAME = "qdrant"  # Not chroma

        # Mock SearchResult objects
        from providers.vectorstore import SearchResult

        source.get.return_value = [
            SearchResult(id="id1", document="doc1", metadata={"k": "v1"}),
            SearchResult(id="id2", document="doc2", metadata={"k": "v2"}),
        ]

        target = MagicMock()

        migrator = VectorStoreMigrator(source, target)
        result = migrator._read_batch("test_collection", 0, 10)

        assert result["ids"] == ["id1", "id2"]
        assert result["documents"] == ["doc1", "doc2"]
        assert result["embeddings"] is None  # No embeddings for non-Chroma
        source.get.assert_called_once_with(collection="test_collection", limit=10, offset=0)

    def test_verification_count_mismatch(self) -> None:
        """Test _verify_integrity with count mismatch (line 384)."""
        source = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                    {"id": "d2", "document": "Doc 2", "metadata": {}, "embedding": [0.2]},
                ],
            }
        )
        # Target has fewer documents - will cause mismatch
        target = MockVectorStoreProvider(
            {
                "docs": [
                    {"id": "d1", "document": "Doc 1", "metadata": {}, "embedding": [0.1]},
                ],
            }
        )

        migrator = VectorStoreMigrator(source, target)
        result = migrator._verify_integrity(["docs"])

        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "Count mismatch" in result["errors"][0]
        assert "source=2" in result["errors"][0]
        assert "target=1" in result["errors"][0]

    def test_verification_exception(self) -> None:
        """Test _verify_integrity when count raises exception (lines 393-394)."""
        source = MagicMock()
        source.count.side_effect = RuntimeError("Database error")
        target = MagicMock()

        migrator = VectorStoreMigrator(source, target)
        result = migrator._verify_integrity(["docs"])

        assert result["success"] is True  # No count mismatches recorded as errors
        assert len(result["warnings"]) == 1
        assert "Could not verify" in result["warnings"][0]
        assert "Database error" in result["warnings"][0]

    def test_migrate_chroma_provider_path(self) -> None:
        """Test migration with Chroma provider to exercise _read_chroma_batch."""
        source = MagicMock()
        source.NAME = "chroma"
        source.list_collections.return_value = ["docs"]
        source.collection_exists.return_value = True
        source.count.return_value = 2

        # Mock the Chroma service chain
        mock_service = MagicMock()
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [{"k": "v1"}, {"k": "v2"}],
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
        }
        mock_service.get_collection.return_value = mock_collection
        source._get_service.return_value = mock_service

        target = MagicMock()
        target.collection_exists.return_value = False
        target.count.return_value = 2

        migrator = VectorStoreMigrator(source, target)
        result = migrator.migrate(verify=False)

        assert result.success is True
        assert result.documents_migrated == 2
        target.add.assert_called()
