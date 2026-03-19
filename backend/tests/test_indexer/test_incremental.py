"""Tests for Incremental Indexer.

Tests cover:
- TC-2.5.1: Handle created file
- TC-2.5.2: Handle modified file
- TC-2.5.3: Handle deleted file
- TC-2.5.4: Content hash detection
- TC-2.5.5: Process batch events
- TC-2.5.6: Sync directory
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.indexer.incremental import IncrementalIndexer, IncrementalResult
from src.indexer.watcher import FileEvent, FileEventType
from src.services.chroma_service import reset_chroma_service
from src.utils.config import IndexerConfig


class MockEmbeddingProvider:
    """Mock embedding provider for testing."""
    
    NAME = "mock"
    dimension = 768
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in texts]
    
    def embed_query(self, query: str) -> list[float]:
        return [0.1] * 768
    
    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> list[list[float]]:
        return [[0.1] * 768 for _ in texts]


@pytest.fixture
def indexer_config() -> IndexerConfig:
    """Create test indexer configuration."""
    return IndexerConfig(
        chunk_size=200,
        chunk_overlap=20,
        max_file_size=1024 * 1024,
        file_types=[".py", ".ts", ".js", ".md", ".vue"],
        exclude_dirs=["node_modules", ".git", "__pycache__"],
    )


@pytest.fixture
def mock_embedding() -> MockEmbeddingProvider:
    """Create mock embedding provider."""
    return MockEmbeddingProvider()


@pytest.fixture
def test_collection(tmp_path: Path):
    """Create a test Chroma collection."""
    import chromadb
    
    reset_chroma_service()
    persist_dir = tmp_path / "chroma"
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection("test_incremental")
    
    yield collection
    
    # Cleanup
    try:
        client.delete_collection("test_incremental")
    except Exception:
        pass


@pytest.fixture
def mock_indexer(mock_embedding: MockEmbeddingProvider, test_collection, indexer_config):
    """Create a mock indexer for testing."""
    from src.indexer.indexer import Indexer
    
    indexer = Indexer(
        config=indexer_config,
        embedding_provider=mock_embedding,
        collection=test_collection,
    )
    return indexer


@pytest.fixture
def incremental_indexer(mock_indexer, test_collection, indexer_config):
    """Create an IncrementalIndexer instance for testing."""
    return IncrementalIndexer(
        indexer=mock_indexer,
        collection=test_collection,
        config=indexer_config,
    )


class TestIncrementalResult:
    """IncrementalResult 测试类"""

    def test_default_values(self):
        """测试默认值"""
        result = IncrementalResult()
        
        assert result.files_added == 0
        assert result.files_updated == 0
        assert result.files_deleted == 0
        assert result.chunks_added == 0
        assert result.chunks_removed == 0
        assert result.errors == []

    def test_with_values(self):
        """测试带值的创建"""
        result = IncrementalResult(
            files_added=5,
            files_updated=3,
            files_deleted=2,
            chunks_added=50,
            chunks_removed=20,
            errors=["error1"],
        )
        
        assert result.files_added == 5
        assert result.files_updated == 3
        assert result.files_deleted == 2
        assert result.chunks_added == 50
        assert result.chunks_removed == 20
        assert len(result.errors) == 1


class TestIncrementalIndexer:
    """IncrementalIndexer 测试类"""

    def test_handle_created_file(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """TC-2.5.1: 处理新创建文件"""
        # Create a test file
        test_file = tmp_path / "new_file.py"
        test_file.write_text("""
def hello():
    '''Say hello.'''
    print("Hello, World!")
""")
        
        # Handle created event
        chunks = incremental_indexer.handle_created(test_file)
        
        # Verify chunks were created
        assert chunks > 0
        
        # Verify chunks in collection
        results = incremental_indexer._collection.get(
            where={"source": str(test_file)}
        )
        assert len(results["ids"]) == chunks
        
        # Verify content_hash in metadata
        if results["metadatas"]:
            assert "content_hash" in results["metadatas"][0]

    def test_handle_modified_file(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """TC-2.5.2: 处理修改文件"""
        # Create and index initial file
        test_file = tmp_path / "modified.py"
        test_file.write_text("def old(): pass")
        
        initial_chunks = incremental_indexer.handle_created(test_file)
        assert initial_chunks > 0
        
        # Modify the file
        test_file.write_text("""
def new_function():
    '''This is a new function.'''
    return "new"

def another_function():
    '''Another function.'''
    return "another"
""")
        
        # Handle modified event
        removed, added = incremental_indexer.handle_modified(test_file)
        
        # Verify old chunks removed, new chunks added
        assert removed == initial_chunks
        assert added > 0
        
        # Verify only new content in collection
        results = incremental_indexer._collection.get(
            where={"source": str(test_file)}
        )
        assert len(results["ids"]) == added

    def test_handle_deleted_file(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """TC-2.5.3: 处理删除文件"""
        # Create and index a file
        test_file = tmp_path / "to_delete.py"
        test_file.write_text("def delete_me(): pass")
        
        chunks = incremental_indexer.handle_created(test_file)
        assert chunks > 0
        
        # Delete the file (don't actually delete from disk for test)
        # Handle deleted event
        removed = incremental_indexer.handle_deleted(test_file)
        
        # Verify chunks removed
        assert removed == chunks
        
        # Verify no chunks in collection
        results = incremental_indexer._collection.get(
            where={"source": str(test_file)}
        )
        assert len(results["ids"]) == 0

    def test_content_hash_detection(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """TC-2.5.4: 内容hash变更检测"""
        # Create and index file
        test_file = tmp_path / "hash_test.py"
        test_file.write_text("x = 1")
        
        chunks1 = incremental_indexer.handle_created(test_file)
        
        # Try to "modify" with same content
        test_file.write_text("x = 1")  # Same content
        
        removed, added = incremental_indexer.handle_modified(test_file)
        
        # Should detect no change
        assert removed == 0
        assert added == 0

    def test_process_events(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """TC-2.5.5: 处理批量事件"""
        # Create files
        file1 = tmp_path / "file1.py"
        file1.write_text("def one(): pass")
        
        file2 = tmp_path / "file2.py"
        file2.write_text("def two(): pass")
        
        file3 = tmp_path / "file3.py"
        file3.write_text("def three(): pass")
        
        # Create events
        events = [
            FileEvent(FileEventType.CREATED, file1, False),
            FileEvent(FileEventType.CREATED, file2, False),
            FileEvent(FileEventType.CREATED, file3, False),
        ]
        
        result = incremental_indexer.process_events(events)
        
        assert result.files_added == 3
        assert result.chunks_added > 0
        assert len(result.errors) == 0

    def test_process_mixed_events(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试处理混合事件"""
        # Create files
        create_file = tmp_path / "create.py"
        create_file.write_text("def new(): pass")
        
        modify_file = tmp_path / "modify.py"
        modify_file.write_text("def old(): pass")
        incremental_indexer.handle_created(modify_file)
        
        modify_file.write_text("def new(): pass")  # Modify
        
        delete_file = tmp_path / "delete.py"
        delete_file.write_text("def del(): pass")
        incremental_indexer.handle_created(delete_file)
        
        # Process mixed events
        events = [
            FileEvent(FileEventType.CREATED, create_file, False),
            FileEvent(FileEventType.MODIFIED, modify_file, False),
            FileEvent(FileEventType.DELETED, delete_file, False),
        ]
        
        result = incremental_indexer.process_events(events)
        
        assert result.files_added == 1
        assert result.files_updated == 1
        assert result.files_deleted == 1

    def test_sync_directory(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """TC-2.5.6: 同步目录"""
        # Create directory structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def main(): pass")
        (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
        (tmp_path / "README.md").write_text("# Test")
        
        # Sync directory
        result = incremental_indexer.sync_directory(tmp_path)
        
        assert result.files_added >= 2  # At least .py files
        assert result.chunks_added > 0
        assert len(result.errors) == 0

    def test_sync_with_existing_index(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试同步已索引目录"""
        # Create and index initial files
        (tmp_path / "file1.py").write_text("def one(): pass")
        (tmp_path / "file2.py").write_text("def two(): pass")
        
        incremental_indexer.sync_directory(tmp_path)
        
        # Modify one file, add one file, delete one file
        (tmp_path / "file1.py").write_text("def modified(): pass")
        (tmp_path / "file3.py").write_text("def three(): pass")
        (tmp_path / "file2.py").unlink()
        
        # Sync again
        result = incremental_indexer.sync_directory(tmp_path)
        
        assert result.files_added >= 1  # file3
        assert result.files_updated >= 1  # file1
        assert result.files_deleted >= 1  # file2

    def test_sync_empty_directory(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试同步空目录"""
        result = incremental_indexer.sync_directory(tmp_path)
        
        assert result.files_added == 0
        assert result.files_updated == 0
        assert result.files_deleted == 0

    def test_nonexistent_file(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试处理不存在的文件"""
        nonexistent = tmp_path / "nonexistent.py"
        
        chunks = incremental_indexer.handle_created(nonexistent)
        assert chunks == 0
        
        removed, added = incremental_indexer.handle_modified(nonexistent)
        assert removed == 0
        assert added == 0

    def test_empty_file(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试处理空文件"""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        
        chunks = incremental_indexer.handle_created(empty_file)
        assert chunks == 0


class TestContentHashStorage:
    """Content Hash 存储测试"""

    def test_hash_stored_in_metadata(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试hash存储在metadata中"""
        test_file = tmp_path / "hash_storage.py"
        test_file.write_text("def test(): pass")
        
        incremental_indexer.handle_created(test_file)
        
        # Get all chunks for this file
        results = incremental_indexer._collection.get(
            where={"source": str(test_file)}
        )
        
        assert len(results["metadatas"]) > 0
        assert "content_hash" in results["metadatas"][0]
        assert len(results["metadatas"][0]["content_hash"]) == 32  # MD5 hex

    def test_different_content_different_hash(
        self,
        incremental_indexer: IncrementalIndexer,
        tmp_path: Path,
    ):
        """测试不同内容产生不同hash"""
        file1 = tmp_path / "file1.py"
        file1.write_text("x = 1")
        
        file2 = tmp_path / "file2.py"
        file2.write_text("y = 2")
        
        incremental_indexer.handle_created(file1)
        incremental_indexer.handle_created(file2)
        
        results1 = incremental_indexer._collection.get(
            where={"source": str(file1)}
        )
        results2 = incremental_indexer._collection.get(
            where={"source": str(file2)}
        )
        
        hash1 = results1["metadatas"][0]["content_hash"]
        hash2 = results2["metadatas"][0]["content_hash"]
        
        assert hash1 != hash2