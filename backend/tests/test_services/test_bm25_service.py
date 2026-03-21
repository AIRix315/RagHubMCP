"""Tests for BM25 service.

Tests cover:
- TC-BM25-1: BM25Index add_documents edge cases
- TC-BM25-2: BM25Index query boundary conditions
- TC-BM25-3: BM25Index persistence errors
- TC-BM25-4: BM25Service index loading failures
- TC-BM25-5: BM25Service empty input handling
- TC-BM25-6: BM25Service index management
- TC-BM25-7: BM25Service count edge cases
- TC-BM25-8: BM25Service reset functionality
- TC-BM25-9: get_bm25_service configuration errors
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.bm25_service import (
    BM25Index,
    BM25Service,
    get_bm25_service,
    reset_bm25_service,
)


class TestBM25IndexAddDocuments:
    """Tests for BM25Index.add_documents edge cases."""

    def test_add_documents_with_duplicate_id_logs_warning(self, caplog):
        """TC-BM25-1.1: Adding document with duplicate ID logs warning."""
        import logging

        caplog.set_level(logging.WARNING)

        index = BM25Index()
        index.index_documents(["Document one"], ["id1"])

        # Add document with duplicate ID
        index.add_documents(["Document two"], ["id1"])

        # Should log warning about duplicate
        assert any("already exists" in record.message for record in caplog.records)

    def test_add_documents_replaces_existing_content(self):
        """TC-BM25-1.2: Adding document with duplicate ID replaces content."""
        index = BM25Index()
        index.index_documents(["Original document about Python"], ["doc1"])

        # Add new content for same ID
        index.add_documents(["New document about JavaScript"], ["doc1"])

        # Should have only 1 document (replaced)
        assert index.count() == 1

        # Query for JavaScript should now match
        results = index.query("JavaScript", k=1)
        assert len(results) == 1
        assert results[0][0] == "doc1"

    def test_add_documents_appends_new_ids(self):
        """TC-BM25-1.3: Adding documents with new IDs appends to index."""
        index = BM25Index()
        index.index_documents(["Document one"], ["id1"])

        # Add new documents
        index.add_documents(["Document two", "Document three"], ["id2", "id3"])

        assert index.count() == 3
        assert "id1" in index.doc_id_to_idx
        assert "id2" in index.doc_id_to_idx
        assert "id3" in index.doc_id_to_idx


class TestBM25IndexQuery:
    """Tests for BM25Index.query boundary conditions."""

    def test_query_returns_empty_when_k_is_zero(self):
        """TC-BM25-2.1: Query with k=0 returns empty list."""
        index = BM25Index()
        index.index_documents(["Document one", "Document two"], ["id1", "id2"])

        results = index.query("Document", k=0)

        assert results == []

    def test_query_with_k_greater_than_document_count(self):
        """TC-BM25-2.2: Query with k > doc count returns all documents."""
        index = BM25Index()
        index.index_documents(["Doc one", "Doc two"], ["id1", "id2"])

        results = index.query("Doc", k=100)

        # Should return at most 2 (number of documents)
        assert len(results) == 2


class TestBM25IndexPersistence:
    """Tests for BM25Index save/load errors."""

    def test_save_without_index_raises_value_error(self, tmp_path: Path):
        """TC-BM25-3.1: Saving without initializing index raises ValueError."""
        index = BM25Index()

        with pytest.raises(ValueError, match="No index to save"):
            index.save(tmp_path / "bm25_test")

    def test_load_nonexistent_path_raises_filenotfound(self, tmp_path: Path):
        """TC-BM25-3.2: Loading from nonexistent path raises FileNotFoundError."""
        index = BM25Index()

        nonexistent_path = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError, match="Index path not found"):
            index.load(nonexistent_path)

    def test_save_and_load_preserves_doc_ids(self, tmp_path: Path):
        """TC-BM25-3.3: Save and load preserves document IDs."""
        index = BM25Index()
        documents = ["Python tutorial", "JavaScript guide", "Go handbook"]
        ids = ["py", "js", "go"]

        index.index_documents(documents, ids)

        save_path = tmp_path / "bm25_persist"
        index.save(save_path)

        # Load into new index
        new_index = BM25Index()
        new_index.load(save_path)

        # Verify doc_ids are preserved
        assert new_index.doc_ids == ids
        assert new_index.count() == 3


class TestBM25ServiceIndexLoading:
    """Tests for BM25Service get_or_create_index loading failures."""

    def test_get_or_create_index_handles_load_failure(self, tmp_path: Path, caplog):
        """TC-BM25-4.1: get_or_create_index handles corrupted index gracefully."""
        import logging

        caplog.set_level(logging.WARNING)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted index files
        collection_dir = persist_dir / "corrupted_collection"
        collection_dir.mkdir(parents=True, exist_ok=True)

        # Create incomplete/corrupted index files
        (collection_dir / "bm25_index").mkdir()
        (collection_dir / "metadata.json").write_text("{invalid json")

        service = get_bm25_service(str(persist_dir))

        # Should not raise, but log warning
        index = service.get_or_create_index("corrupted_collection")

        assert index is not None
        assert any("Failed to load" in record.message for record in caplog.records)

        reset_bm25_service()

    def test_get_or_create_index_loads_existing_valid_index(self, tmp_path: Path):
        """TC-BM25-4.2: get_or_create_index loads valid existing index."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"

        # First, create and save an index
        service = BM25Service(persist_dir=str(persist_dir))
        service.index_documents("test_coll", ["Document one"], ["id1"])
        service.save_index("test_coll")

        # Reset to simulate new service instance
        new_service = BM25Service(persist_dir=str(persist_dir))

        # Get or create should load existing index
        index = new_service.get_or_create_index("test_coll")

        assert index.count() == 1


class TestBM25ServiceEmptyInputs:
    """Tests for BM25Service empty input handling."""

    def test_index_documents_empty_list_logs_warning(self, tmp_path: Path, caplog):
        """TC-BM25-5.1: Indexing empty documents list logs warning."""
        import logging

        caplog.set_level(logging.WARNING)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.index_documents("test_coll", [], [])

        assert any("No documents to index" in record.message for record in caplog.records)

        reset_bm25_service()

    def test_index_documents_empty_list_does_not_create_index(self, tmp_path: Path):
        """TC-BM25-5.2: Indexing empty list does not create index."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.index_documents("test_coll", [], [])

        # Collection should not be in indexed collections
        assert "test_coll" not in service.list_indexed_collections()

        reset_bm25_service()

    def test_add_documents_empty_list_logs_warning(self, tmp_path: Path, caplog):
        """TC-BM25-5.3: Adding empty documents list logs warning."""
        import logging

        caplog.set_level(logging.WARNING)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.add_documents("test_coll", [], [])

        assert any("No documents to add" in record.message for record in caplog.records)

        reset_bm25_service()

    def test_add_documents_empty_list_to_existing_index(self, tmp_path: Path):
        """TC-BM25-5.4: Adding empty list to existing index preserves it."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        # Create initial index
        service.index_documents("test_coll", ["Doc one"], ["id1"])
        assert service.count("test_coll") == 1

        # Add empty list
        service.add_documents("test_coll", [], [])

        # Index should still have 1 document
        assert service.count("test_coll") == 1

        reset_bm25_service()

    def test_add_documents_to_collection_success(self, tmp_path: Path, caplog):
        """TC-BM25-5.5: Adding documents to existing collection succeeds."""
        import logging

        caplog.set_level(logging.INFO)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        # Create initial index
        service.index_documents("test_coll", ["Doc one"], ["id1"])

        # Add new documents
        service.add_documents("test_coll", ["Doc two", "Doc three"], ["id2", "id3"])

        # Should have 3 documents now
        assert service.count("test_coll") == 3

        # Should log success
        assert any("Added 2 documents" in record.message for record in caplog.records)

        reset_bm25_service()


class TestBM25ServiceIndexManagement:
    """Tests for BM25Service index management methods."""

    def test_save_index_nonexistent_collection_logs_warning(self, tmp_path: Path, caplog):
        """TC-BM25-6.1: Saving nonexistent collection index logs warning."""
        import logging

        caplog.set_level(logging.WARNING)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.save_index("nonexistent_coll")

        assert any("No index found" in record.message for record in caplog.records)

        reset_bm25_service()

    def test_load_index_nonexistent_collection_returns_false(self, tmp_path: Path):
        """TC-BM25-6.2: Loading nonexistent collection index returns False."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        result = service.load_index("nonexistent_coll")

        assert result is False

        reset_bm25_service()

    def test_load_index_corrupted_files_returns_false(self, tmp_path: Path, caplog):
        """TC-BM25-6.3: Loading corrupted index returns False."""
        import logging

        caplog.set_level(logging.ERROR)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted index directory
        coll_dir = persist_dir / "corrupted"
        coll_dir.mkdir(parents=True, exist_ok=True)
        (coll_dir / "bm25_index").mkdir()
        (coll_dir / "metadata.json").write_text("{bad json")

        service = get_bm25_service(str(persist_dir))
        result = service.load_index("corrupted")

        assert result is False
        assert any("Failed to load" in record.message for record in caplog.records)

        reset_bm25_service()

    def test_delete_index_removes_disk_files(self, tmp_path: Path):
        """TC-BM25-6.4: delete_index removes index from disk."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        # Create and save index
        service.index_documents("to_delete", ["Document"], ["id1"])
        service.save_index("to_delete")

        index_path = persist_dir / "to_delete"
        assert index_path.exists()

        # Delete index
        service.delete_index("to_delete")

        # Verify disk deletion
        assert not index_path.exists()
        assert "to_delete" not in service.list_indexed_collections()

        reset_bm25_service()

    def test_delete_nonexistent_index_does_not_raise(self, tmp_path: Path):
        """TC-BM25-6.5: Deleting nonexistent index does not raise."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        # Should not raise
        service.delete_index("nonexistent")

        reset_bm25_service()


class TestBM25ServiceCount:
    """Tests for BM25Service.count edge cases."""

    def test_count_nonexistent_collection_returns_zero(self, tmp_path: Path):
        """TC-BM25-7.1: Counting nonexistent collection returns 0."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        count = service.count("nonexistent_coll")

        assert count == 0

        reset_bm25_service()

    def test_count_after_indexing_returns_correct_count(self, tmp_path: Path):
        """TC-BM25-7.2: Count returns correct number after indexing."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.index_documents("test_coll", ["Doc 1", "Doc 2", "Doc 3"], ["id1", "id2", "id3"])

        assert service.count("test_coll") == 3

        reset_bm25_service()


class TestBM25ServiceReset:
    """Tests for BM25Service.reset functionality."""

    def test_reset_clears_all_indexes(self, tmp_path: Path, caplog):
        """TC-BM25-8.1: Reset clears all in-memory indexes."""
        import logging

        caplog.set_level(logging.WARNING)

        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        # Create multiple indexes
        service.index_documents("coll1", ["Doc"], ["id1"])
        service.index_documents("coll2", ["Doc"], ["id1"])

        assert len(service.list_indexed_collections()) == 2

        # Reset
        service.reset()

        assert len(service.list_indexed_collections()) == 0
        assert any("Reset BM25Service" in record.message for record in caplog.records)

        reset_bm25_service()

    def test_reset_does_not_delete_disk_files(self, tmp_path: Path):
        """TC-BM25-8.2: Reset does not delete persisted files."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        # Create and save index
        service.index_documents("persist_test", ["Document"], ["id1"])
        service.save_index("persist_test")

        index_path = persist_dir / "persist_test"
        assert index_path.exists()

        # Reset
        service.reset()

        # Disk files should still exist
        assert index_path.exists()

        reset_bm25_service()


class TestGetBM25Service:
    """Tests for get_bm25_service configuration handling."""

    def test_get_bm25_service_without_persist_dir_raises_on_first_call(self):
        """TC-BM25-9.1: First call without persist_dir raises ValueError when no config."""
        reset_bm25_service()

        with patch("utils.config.get_config", side_effect=RuntimeError("No config")):
            with pytest.raises(ValueError, match="persist_dir must be provided"):
                get_bm25_service()

        reset_bm25_service()

    def test_get_bm25_service_without_persist_dir_raises_attribute_error(self):
        """TC-BM25-9.2: First call raises ValueError when config missing hybrid settings."""
        reset_bm25_service()

        mock_config = MagicMock()
        # Simulate missing hybrid attribute
        del mock_config.hybrid

        with patch("utils.config.get_config", return_value=mock_config):
            with pytest.raises(ValueError, match="persist_dir must be provided"):
                get_bm25_service()

        reset_bm25_service()

    def test_get_bm25_service_loads_persist_dir_from_config(self):
        """TC-BM25-9.3: Service loads persist_dir from config when not provided."""
        reset_bm25_service()

        mock_config = MagicMock()
        mock_config.hybrid.bm25_persist_dir = "/config/bm25/path"

        with patch("utils.config.get_config", return_value=mock_config):
            service = get_bm25_service()

        assert service.persist_dir == Path("/config/bm25/path")

        reset_bm25_service()


class TestBM25IndexWithCustomStopwords:
    """Tests for BM25Index with different stopwords settings."""

    def test_index_documents_with_custom_stopwords(self):
        """TC-BM25-10.1: Index documents with non-English stopwords."""
        index = BM25Index()

        documents = ["Le chat noir", "La maison blanche"]
        ids = ["fr1", "fr2"]

        # Should not raise with French stopwords
        index.index_documents(documents, ids, stopwords="fr")

        assert index.count() == 2

    def test_add_documents_with_custom_stopwords(self):
        """TC-BM25-10.2: Add documents with custom stopwords."""
        index = BM25Index()
        index.index_documents(["English document"], ["en1"])

        # Add with different stopwords
        index.add_documents(["German document"], ["de1"], stopwords="de")

        assert index.count() == 2


class TestBM25ServicePersistence:
    """Tests for BM25Service persistence operations."""

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        """TC-BM25-11.1: Save and load preserves document count and IDs."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        documents = [
            "Python is a programming language",
            "JavaScript runs in browsers",
            "Go is efficient for concurrency",
        ]
        ids = ["py", "js", "go"]

        service.index_documents("roundtrip_test", documents, ids)
        service.save_index("roundtrip_test")

        # Create new service instance
        reset_bm25_service()
        new_service = get_bm25_service(str(persist_dir))
        loaded = new_service.load_index("roundtrip_test")

        # Verify load succeeded
        assert loaded is True
        assert new_service.count("roundtrip_test") == 3

        reset_bm25_service()
