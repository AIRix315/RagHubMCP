"""Tests for LineChunker.

Test cases:
- TC-1.9.3: LineChunker 切分正确
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestLineChunker:
    """TC-1.9.3: LineChunker 切分正确"""

    def test_line_based_splitting(self):
        """TC-1.9.3: Text is split by lines, not characters."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=5, overlap=0)
        
        # Create text with 15 lines
        lines = [f"Line {i}" for i in range(15)]
        text = "\n".join(lines)
        chunks = chunker.chunk(text)
        
        # Should have 3 chunks (15 lines / 5 lines per chunk)
        assert len(chunks) == 3
        
        # Each chunk should have at most 5 lines
        for chunk in chunks:
            chunk_lines = chunk.text.rstrip("\n").split("\n")
            assert len(chunk_lines) <= 5

    def test_line_count_respected(self):
        """TC-1.9.3: chunk_size limits lines, not characters."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=3, overlap=0)
        
        # Long lines but only 9 total
        lines = ["a" * 100 for _ in range(9)]
        text = "\n".join(lines)
        chunks = chunker.chunk(text)
        
        # Should have 3 chunks
        assert len(chunks) == 3
        
        # Each chunk should have exactly 3 lines
        for chunk in chunks:
            chunk_lines = [l for l in chunk.text.split("\n") if l]
            assert len(chunk_lines) <= 3

    def test_preserves_line_boundaries(self):
        """TC-1.9.3: Line boundaries are preserved."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=3, overlap=0)
        
        lines = ["line1", "line2", "line3", "line4", "line5"]
        text = "\n".join(lines)
        chunks = chunker.chunk(text)
        
        # First chunk: lines 1-3
        assert "line1" in chunks[0].text
        assert "line2" in chunks[0].text
        assert "line3" in chunks[0].text
        assert "line4" not in chunks[0].text
        
        # Second chunk: lines 4-5
        assert "line4" in chunks[1].text
        assert "line5" in chunks[1].text

    def test_empty_text_returns_empty_list(self):
        """Empty text returns empty chunk list."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=5, overlap=1)
        chunks = chunker.chunk("")
        
        assert chunks == []

    def test_single_line_text(self):
        """Single line text returns one chunk."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=5, overlap=1)
        text = "single line without newline"
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_line_overlap(self):
        """TC-1.9.3: Overlap works with lines."""
        from chunkers.line import LineChunker
        
        # chunk_size=5, overlap=2 -> step=3
        chunker = LineChunker(chunk_size=5, overlap=2)
        
        lines = [f"Line{i}" for i in range(10)]
        text = "\n".join(lines)
        chunks = chunker.chunk(text)
        
        # Verify that we have multiple chunks
        assert len(chunks) >= 2
        
        # Check that consecutive chunks share lines
        # With step=3: chunk 0 covers lines 0-4, chunk 1 covers lines 3-7
        # So lines 3-4 should appear in both
        if len(chunks) >= 2:
            # line_start is 1-indexed
            assert chunks[1].metadata["line_start"] <= chunks[0].metadata["line_end"]

    def test_positions_accurate(self):
        """TC-1.9.3: Character positions are accurate."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=2, overlap=0)
        
        text = "abc\ndef\nghi\njkl"
        chunks = chunker.chunk(text)
        
        # Verify positions
        for chunk in chunks:
            extracted = text[chunk.start:chunk.end]
            assert extracted == chunk.text

    def test_metadata_includes_line_info(self):
        """TC-1.9.3: Metadata includes line numbers."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=3, overlap=0)
        
        lines = [f"Line {i}" for i in range(6)]
        text = "\n".join(lines)
        chunks = chunker.chunk(text)
        
        # First chunk: lines 1-3
        assert chunks[0].metadata["line_start"] == 1
        assert chunks[0].metadata["line_end"] == 3
        
        # Second chunk: lines 4-6
        assert chunks[1].metadata["line_start"] == 4
        assert chunks[1].metadata["line_end"] == 6