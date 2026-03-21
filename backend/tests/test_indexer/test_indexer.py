"""Tests for Indexer.

Tests cover:
- TC-1.10.1: 索引单个文件成功
- TC-1.10.2: 索引目录成功
- TC-1.10.3: 进度回调正确触发
- TC-1.10.4: 入库后可检索到内容
- TC-1.10.5: 大批量索引不 OOM (batch_size 控制)
- TC-1.10.6: 不同文件类型使用正确 chunker
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.chunkers import Chunk
from src.indexer.indexer import Indexer, IndexResult
from src.providers.embedding.base import BaseEmbeddingProvider
from src.providers.vectorstore.base import BaseVectorStoreProvider
from src.utils.config import IndexerConfig


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock embedding provider for testing."""
    
    NAME = "mock"
    
    @property
    def dimension(self) -> int:
        return 768
    
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
    
    @classmethod
    def from_config(cls, config: dict) -> "MockEmbeddingProvider":
        return cls()


@pytest.fixture
def indexer_config() -> IndexerConfig:
    """Create test indexer configuration."""
    return IndexerConfig(
        chunk_size=200,
        chunk_overlap=20,
        max_file_size=1024 * 1024,  # 1MB
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
    
    persist_dir = tmp_path / "chroma"
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection("test_index")
    
    yield collection
    
    # Cleanup
    try:
        client.delete_collection("test_index")
    except Exception:
        pass


@pytest.fixture
def test_vectorstore(tmp_path: Path, mock_embedding: MockEmbeddingProvider) -> BaseVectorStoreProvider:
    """Create a test vectorstore provider."""
    from src.providers.vectorstore.chroma import ChromaProvider
    
    persist_dir = tmp_path / "chroma_vs"
    return ChromaProvider(
        persist_dir=str(persist_dir),
        embedding_provider=mock_embedding,
    )


@pytest.fixture
def indexer(
    indexer_config: IndexerConfig,
    mock_embedding: MockEmbeddingProvider,
    test_vectorstore: BaseVectorStoreProvider,
) -> Indexer:
    """Create an Indexer instance for testing."""
    return Indexer(
        config=indexer_config,
        embedding_provider=mock_embedding,
        vectorstore=test_vectorstore,
        collection_name="test_index",
    )


class TestIndexer:
    """Indexer 测试类"""

    def test_index_single_file_success(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """TC-1.10.1: 索引单个文件成功"""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def hello():
    '''Say hello.'''
    print("Hello, World!")

def goodbye():
    '''Say goodbye.'''
    print("Goodbye!")
""")
        
        # Index the file
        chunk_count = indexer.index_file(test_file)
        
        # Verify
        assert chunk_count > 0

    def test_index_directory_success(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """TC-1.10.2: 索引目录成功"""
        # Create directory structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
        (tmp_path / "README.md").write_text("# Test Project")
        
        # Index the directory
        result = indexer.index_directory(tmp_path)
        
        # Verify
        assert result.files_indexed >= 2  # At least .py files
        assert result.chunks_created > 0
        assert len(result.errors) == 0

    def test_progress_callback_triggered(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """TC-1.10.3: 进度回调正确触发"""
        # Create test files
        (tmp_path / "file1.py").write_text("x = 1")
        (tmp_path / "file2.py").write_text("y = 2")
        
        # Track progress calls
        progress_calls: list[tuple[int, int, str]] = []
        
        def on_progress(current: int, total: int, message: str):
            progress_calls.append((current, total, message))
        
        # Index with progress callback
        indexer.index_directory(tmp_path, on_progress=on_progress)
        
        # Verify progress was called
        assert len(progress_calls) > 0
        
        # Check that we have at least one completion call
        final_call = progress_calls[-1]
        assert "Completed" in final_call[2] or "Indexing" in final_call[2]

    def test_search_after_index(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """TC-1.10.4: 入库后可检索到内容"""
        # Create and index a file with unique content
        test_file = tmp_path / "unique.py"
        test_file.write_text("""
def unique_function_xyz():
    '''This is a unique function for testing search.'''
    return "xyz123"
""")
        
        indexer.index_file(test_file)
        
        # Search for the content
        results = indexer.search("unique function", n_results=5)
        
        # Verify
        assert len(results) > 0
        assert "unique_function_xyz" in results[0]["document"]

    def test_large_batch_no_oom(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """TC-1.10.5: 大批量索引不 OOM (batch_size 控制)"""
        # Create a large file that will generate many chunks
        large_content = "\n".join([
            f"def function_{i}():\n    '''Function {i} docstring.'''\n    return {i}"
            for i in range(100)
        ])
        
        test_file = tmp_path / "large.py"
        test_file.write_text(large_content)
        
        # Index the file - should not raise MemoryError
        chunk_count = indexer.index_file(test_file)
        
        # Verify chunks were created
        assert chunk_count > 0
        
        # Verify we can search the indexed content
        results = indexer.search("function", n_results=10)
        assert len(results) > 0

    def test_different_file_types_use_correct_chunker(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """TC-1.10.6: 不同文件类型使用正确 chunker"""
        # Create files of different types
        py_file = tmp_path / "test.py"
        py_file.write_text("def test(): pass")
        
        md_file = tmp_path / "README.md"
        md_file.write_text("# Title\n\nParagraph content.\n\n## Section\n\nMore content.")
        
        ts_file = tmp_path / "app.ts"
        ts_file.write_text("const x: number = 1;")
        
        # Index all files
        py_chunks = indexer.index_file(py_file)
        md_chunks = indexer.index_file(md_file)
        ts_chunks = indexer.index_file(ts_file)
        
        # All should create chunks
        assert py_chunks > 0
        assert md_chunks > 0
        assert ts_chunks > 0

    def test_index_empty_file(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """测试索引空文件"""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        
        chunk_count = indexer.index_file(empty_file)
        
        assert chunk_count == 0

    def test_index_file_with_unsupported_extension(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """测试索引不支持的文件类型"""
        unsupported_file = tmp_path / "data.bin"
        unsupported_file.write_text("binary data")
        
        # Should be skipped by scanner
        result = indexer.index_directory(tmp_path)
        
        # No .bin files should be indexed
        assert result.files_indexed == 0

    def test_index_chunks_directly(
        self,
        indexer: Indexer,
    ):
        """测试直接索引 chunks"""
        # Create chunks manually
        chunks = [
            Chunk(text="First chunk content", start=0, end=20, metadata={"source": "test"}),
            Chunk(text="Second chunk content", start=20, end=40, metadata={"source": "test"}),
            Chunk(text="Third chunk content", start=40, end=60, metadata={"source": "test"}),
        ]
        
        # Index chunks
        indexer.index_chunks(chunks, batch_size=2)
        
        # Search should find the content
        results = indexer.search("chunk content", n_results=5)
        assert len(results) >= 3

    def test_clear_indexed_content(
        self,
        indexer: Indexer,
        tmp_path: Path,
    ):
        """测试清除已索引内容"""
        # Index a file
        test_file = tmp_path / "to_clear.py"
        test_file.write_text("def clear_me(): pass")
        
        indexer.index_file(test_file)
        
        # Verify content exists
        results_before = indexer.search("clear_me", n_results=5)
        assert len(results_before) > 0
        
        # Clear
        indexer.clear()
        
        # Verify content is gone
        results_after = indexer.search("clear_me", n_results=5)
        assert len(results_after) == 0


class TestIndexResult:
    """IndexResult 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = IndexResult()
        
        assert result.files_indexed == 0
        assert result.files_skipped == 0
        assert result.chunks_created == 0
        assert result.errors == []

    def test_with_values(self):
        """测试带值的创建"""
        result = IndexResult(
            files_indexed=10,
            files_skipped=2,
            chunks_created=50,
            errors=["error1"],
        )
        
        assert result.files_indexed == 10
        assert result.files_skipped == 2
        assert result.chunks_created == 50
        assert len(result.errors) == 1