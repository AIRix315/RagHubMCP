"""Tests for Chunker base classes.

Test cases:
- Chunk dataclass functionality
- ChunkerPlugin abstract class behavior
- Parameter validation
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestChunkDataclass:
    """Tests for Chunk dataclass."""

    def test_chunk_creation(self):
        """Chunk can be created with required fields."""
        from chunkers.base import Chunk
        
        chunk = Chunk(
            text="Hello world",
            start=0,
            end=11
        )
        
        assert chunk.text == "Hello world"
        assert chunk.start == 0
        assert chunk.end == 11
        assert chunk.metadata == {}

    def test_chunk_with_metadata(self):
        """Chunk can include metadata."""
        from chunkers.base import Chunk
        
        chunk = Chunk(
            text="Test",
            start=0,
            end=4,
            metadata={"source": "test.txt", "lang": "python"}
        )
        
        assert chunk.metadata["source"] == "test.txt"
        assert chunk.metadata["lang"] == "python"

    def test_chunk_len(self):
        """Chunk len() returns text length."""
        from chunkers.base import Chunk
        
        chunk = Chunk(text="Hello", start=0, end=5)
        assert len(chunk) == 5


class TestChunkerPlugin:
    """Tests for ChunkerPlugin abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """ChunkerPlugin cannot be instantiated directly."""
        from chunkers.base import ChunkerPlugin
        
        with pytest.raises(TypeError):
            ChunkerPlugin(chunk_size=100)

    def test_invalid_chunk_size(self):
        """chunk_size must be positive."""
        from chunkers.base import ChunkerPlugin
        
        class TestChunker(ChunkerPlugin):
            NAME = "test"
            
            def chunk(self, text):
                return []
        
        with pytest.raises(ValueError) as exc_info:
            TestChunker(chunk_size=0)
        assert "positive" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            TestChunker(chunk_size=-1)
        assert "positive" in str(exc_info.value)

    def test_invalid_overlap_negative(self):
        """overlap cannot be negative."""
        from chunkers.base import ChunkerPlugin
        
        class TestChunker(ChunkerPlugin):
            NAME = "test"
            
            def chunk(self, text):
                return []
        
        with pytest.raises(ValueError) as exc_info:
            TestChunker(chunk_size=100, overlap=-1)
        assert "negative" in str(exc_info.value)

    def test_invalid_overlap_exceeds_size(self):
        """overlap must be less than chunk_size."""
        from chunkers.base import ChunkerPlugin
        
        class TestChunker(ChunkerPlugin):
            NAME = "test"
            
            def chunk(self, text):
                return []
        
        with pytest.raises(ValueError) as exc_info:
            TestChunker(chunk_size=100, overlap=100)
        assert "less than" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            TestChunker(chunk_size=100, overlap=150)
        assert "less than" in str(exc_info.value)

    def test_supports_language_empty_list(self):
        """Empty SUPPORTED_LANGUAGES means universal support."""
        from chunkers.base import ChunkerPlugin
        
        class UniversalChunker(ChunkerPlugin):
            NAME = "universal"
            SUPPORTED_LANGUAGES = []
            
            def chunk(self, text):
                return []
        
        chunker = UniversalChunker()
        assert chunker.supports_language("python") is True
        assert chunker.supports_language("markdown") is True
        assert chunker.supports_language("anything") is True

    def test_supports_language_specific_list(self):
        """Specific SUPPORTED_LANGUAGES limits support."""
        from chunkers.base import ChunkerPlugin
        
        class SpecificChunker(ChunkerPlugin):
            NAME = "specific"
            SUPPORTED_LANGUAGES = ["python", "javascript"]
            
            def chunk(self, text):
                return []
        
        chunker = SpecificChunker()
        assert chunker.supports_language("python") is True
        assert chunker.supports_language("PYTHON") is True  # case-insensitive
        assert chunker.supports_language("javascript") is True
        assert chunker.supports_language("markdown") is False