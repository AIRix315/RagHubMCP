"""Integration tests for Index → Search workflow.

Tests the complete flow:
1. Index files using Indexer
2. Search using MCP chroma_query_with_rerank tool
3. Verify results are correct

TC-1.17.2: test_index_search.py 通过
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import chromadb
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.chunkers import Chunk
from src.indexer.indexer import Indexer, IndexResult
from src.services.chroma_service import reset_chroma_service
from src.utils.config import IndexerConfig


class MockEmbeddingProvider:
    """Mock embedding provider for testing.
    
    Generates deterministic embeddings based on text content.
    """
    
    NAME = "mock"
    dimension = 768
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1 * (i + 1)] * 768 for i, _ in enumerate(texts)]
    
    def embed_query(self, query: str) -> list[float]:
        # Deterministic embedding based on query length
        return [0.5] * 768
    
    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> list[list[float]]:
        return self.embed_documents(texts)


@pytest.fixture
def temp_chroma(tmp_path: Path):
    """Create a temporary ChromaDB instance for testing."""
    reset_chroma_service()
    persist_dir = tmp_path / "chroma"
    client = chromadb.PersistentClient(path=str(persist_dir))
    
    yield client
    
    # Cleanup
    reset_chroma_service()


@pytest.fixture
def mock_embedding() -> MockEmbeddingProvider:
    """Create mock embedding provider."""
    return MockEmbeddingProvider()


@pytest.fixture
def indexer_config() -> IndexerConfig:
    """Create test indexer configuration."""
    return IndexerConfig(
        chunk_size=500,
        chunk_overlap=50,
        max_file_size=1024 * 1024,
        file_types=[".py", ".ts", ".js", ".md", ".vue"],
        exclude_dirs=["node_modules", ".git", "__pycache__"],
    )


class TestIndexSearchIntegration:
    """Integration tests for Index → Search workflow."""

    @pytest.mark.anyio
    async def test_index_then_mcp_search(self, tmp_path: Path, temp_chroma, mock_embedding, indexer_config):
        """TC-INT-1: Index files then search via MCP tool.
        
        Flow:
        1. Create test files
        2. Index using Indexer
        3. Search using MCP chroma_query_with_rerank
        4. Verify results contain indexed content
        """
        # Setup collection
        collection = temp_chroma.get_or_create_collection("test_index_search")
        
        # Create indexer
        indexer = Indexer(
            config=indexer_config,
            embedding_provider=mock_embedding,
            collection=collection,
        )
        
        # Create test files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        
        (src_dir / "main.py").write_text('''
def hello_world():
    """Print hello world message."""
    print("Hello, World!")
    return "hello"

def process_data(data: list) -> dict:
    """Process input data and return result."""
    return {"result": data}
''')
        
        (src_dir / "utils.py").write_text('''
def calculate_sum(numbers: list[int]) -> int:
    """Calculate sum of numbers."""
    return sum(numbers)

def format_output(value: Any) -> str:
    """Format output for display."""
    return f"Result: {value}"
''')
        
        # Step 1: Index files
        result = indexer.index_directory(src_dir)
        
        assert result.files_indexed >= 2
        assert result.chunks_created > 0
        assert len(result.errors) == 0
        
        # Step 2: Search using MCP tool
        from mcp_server.tools.search import register_search_tools
        from mcp_server.server import mcp
        
        # Register tools
        register_search_tools(mcp)
        
        # Mock the chroma service to use our temp client
        with patch('services.get_chroma_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.query = lambda collection_name, query_text, n_results, where: {
                "documents": [doc["document"] for doc in indexer.search(query_text, n_results)],
                "ids": [f"id_{i}" for i in range(min(n_results, result.chunks_created))],
                "metadatas": [doc["metadata"] for doc in indexer.search(query_text, n_results)],
                "distances": [doc["distance"] for doc in indexer.search(query_text, n_results)],
            }
            mock_get_service.return_value = mock_service
            
            # Also mock rerank provider
            with patch('providers.factory.factory.get_rerank_provider') as mock_rerank:
                mock_provider = MagicMock()
                mock_provider.rerank = lambda query, documents, top_k: [
                    type('RerankResult', (), {'index': i, 'text': d, 'score': 0.9 - i * 0.1})()
                    for i, d in enumerate(documents[:top_k])
                ]
                mock_rerank.return_value = mock_provider
                
                # Call MCP tool
                result_json = await mcp.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_index_search",
                    "query": "hello world function",
                    "n_results": 5,
                    "rerank_top_k": 3,
                })
        
        # Step 3: Verify results
        import json
        # result_json is a tuple: (list[TextContent], dict)
        result_data = json.loads(result_json[0][0].text)
        
        assert "results" in result_data
        assert result_data["count"] > 0
        assert result_data["collection"] == "test_index_search"

    def test_index_single_file_search(self, tmp_path: Path, temp_chroma, mock_embedding, indexer_config):
        """TC-INT-2: Index single file and verify search works.
        
        Simpler test for single file indexing.
        """
        collection = temp_chroma.get_or_create_collection("test_single_file")
        
        indexer = Indexer(
            config=indexer_config,
            embedding_provider=mock_embedding,
            collection=collection,
        )
        
        # Create and index single file
        test_file = tmp_path / "test.py"
        test_file.write_text('''
def unique_function_name():
    """This is a unique function for testing."""
    return "unique_result_12345"
''')
        
        chunk_count = indexer.index_file(test_file)
        assert chunk_count > 0
        
        # Search for the unique content
        results = indexer.search("unique function")
        
        assert len(results) > 0
        assert any("unique_function_name" in r["document"] for r in results)

    def test_index_multiple_file_types(self, tmp_path: Path, temp_chroma, mock_embedding, indexer_config):
        """TC-INT-3: Index multiple file types and search across them.
        
        Tests that different file types are properly indexed and searchable.
        """
        collection = temp_chroma.get_or_create_collection("test_multi_types")
        
        indexer = Indexer(
            config=indexer_config,
            embedding_provider=mock_embedding,
            collection=collection,
        )
        
        # Create files of different types
        (tmp_path / "module.py").write_text('def python_function(): pass')
        (tmp_path / "component.ts").write_text('function typescriptFunc(): void {}')
        (tmp_path / "README.md").write_text('# Documentation\n\nThis is documentation.')
        
        result = indexer.index_directory(tmp_path)
        
        assert result.files_indexed >= 3
        
        # Search should find content from all file types
        results = indexer.search("function", n_results=10)
        assert len(results) >= 2

    def test_index_with_metadata_filter(self, tmp_path: Path, temp_chroma, mock_embedding, indexer_config):
        """TC-INT-4: Index files and verify metadata is preserved.
        
        Tests that file metadata (source, language, etc.) is correctly stored.
        """
        collection = temp_chroma.get_or_create_collection("test_metadata")
        
        indexer = Indexer(
            config=indexer_config,
            embedding_provider=mock_embedding,
            collection=collection,
        )
        
        # Create Python file
        py_file = tmp_path / "test.py"
        py_file.write_text('def test_func(): pass')
        
        indexer.index_file(py_file)
        
        # Get all documents and check metadata
        all_docs = collection.get()
        
        assert len(all_docs["ids"]) > 0
        assert len(all_docs["metadatas"]) > 0
        
        # Verify metadata fields
        metadata = all_docs["metadatas"][0]
        assert "source" in metadata
        assert "language" in metadata
        assert metadata["language"] == "python"

    def test_search_after_clear(self, tmp_path: Path, temp_chroma, mock_embedding, indexer_config):
        """TC-INT-5: Verify search returns empty after clearing index.
        
        Tests that clear() properly removes all indexed content.
        """
        collection = temp_chroma.get_or_create_collection("test_clear")
        
        indexer = Indexer(
            config=indexer_config,
            embedding_provider=mock_embedding,
            collection=collection,
        )
        
        # Index a file
        test_file = tmp_path / "test.py"
        test_file.write_text('def function_to_clear(): pass')
        
        indexer.index_file(test_file)
        
        # Verify content is indexed
        results_before = indexer.search("function", n_results=5)
        assert len(results_before) > 0
        
        # Clear the index
        indexer.clear()
        
        # Verify content is removed
        results_after = indexer.search("function", n_results=5)
        assert len(results_after) == 0