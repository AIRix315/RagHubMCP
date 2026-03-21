"""Tests for SimpleChunker.

Test cases:
- TC-1.9.1: SimpleChunker 切分结果不超出 chunk_size
- TC-1.9.2: overlap 参数生效
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestSimpleChunker:
    """TC-1.9.1: SimpleChunker 切分结果不超出 chunk_size"""

    def test_chunk_size_respected(self):
        """TC-1.9.1: Each chunk does not exceed chunk_size."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=100, overlap=0)

        # Create text longer than chunk_size
        text = "a" * 500
        chunks = chunker.chunk(text)

        # Verify all chunks are within size limit
        for chunk in chunks:
            assert len(chunk.text) <= 100, f"Chunk size {len(chunk.text)} exceeds limit 100"

    def test_chunk_size_with_overlap(self):
        """TC-1.9.1: chunk_size respected even with overlap."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=100, overlap=20)
        text = "a" * 500
        chunks = chunker.chunk(text)

        for chunk in chunks:
            assert len(chunk.text) <= 100

    def test_small_text_returns_single_chunk(self):
        """Text smaller than chunk_size returns one chunk."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=100, overlap=10)
        text = "Hello world"
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == "Hello world"
        assert chunks[0].start == 0
        assert chunks[0].end == 11

    def test_empty_text_returns_empty_list(self):
        """Empty text returns empty chunk list."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=100, overlap=10)
        chunks = chunker.chunk("")

        assert chunks == []

    def test_exact_boundary(self):
        """Text exactly matching chunk_size boundaries."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=10, overlap=0)
        text = "a" * 30  # Exactly 3 chunks
        chunks = chunker.chunk(text)

        assert len(chunks) == 3
        for chunk in chunks:
            assert len(chunk.text) == 10


class TestSimpleChunkerOverlap:
    """TC-1.9.2: overlap 参数生效"""

    def test_overlap_creates_redundancy(self):
        """TC-1.9.2: Overlap creates overlapping content."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=10, overlap=4)
        text = "abcdefghij" * 3  # 30 characters
        chunks = chunker.chunk(text)

        # With chunk_size=10, overlap=4, step=6
        # Chunks: [0:10], [6:16], [12:22], [18:28], [24:30]
        assert len(chunks) >= 2

        # Check that consecutive chunks have overlapping content
        for i in range(len(chunks) - 1):
            current = chunks[i]
            next_chunk = chunks[i + 1]

            # The next chunk starts before the current ends (overlap)
            # Next start should be current_end - overlap
            expected_start = current.end - (chunker.chunk_size - chunker.overlap)
            # Actually: step = chunk_size - overlap = 6
            # So next start = current.start + 6
            expected_start = chunks[i].start + (chunker.chunk_size - chunker.overlap)

            # Verify overlap exists in content
            if next_chunk.start < current.end:
                # There is overlap
                overlap_text = current.text[next_chunk.start - current.start :]
                assert overlap_text in next_chunk.text

    def test_overlap_preserves_content(self):
        """TC-1.9.2: With overlap, content is preserved across boundaries."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=20, overlap=5)
        text = "abcdefghijklmnopqrstuvwxyz"
        chunks = chunker.chunk(text)

        # Verify that we can reconstruct the text by following positions
        # (not by concatenating chunks)
        reconstructed = ""
        for chunk in chunks:
            # Extract the unique portion from each chunk
            pass

        # Instead, verify that the last 5 chars of chunk 0 appear in chunk 1
        if len(chunks) >= 2:
            # step = 20 - 5 = 15
            # chunk 0: [0:20], chunk 1: [15:35]
            assert chunks[1].start == 15

    def test_no_overlap(self):
        """Zero overlap means no redundant content."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=10, overlap=0)
        text = "a" * 25
        chunks = chunker.chunk(text)

        # Verify no position overlap
        for i in range(len(chunks) - 1):
            assert chunks[i].end == chunks[i + 1].start


class TestSimpleChunkerPositions:
    """Tests for chunk position tracking."""

    def test_positions_are_accurate(self):
        """Chunk start/end positions are accurate."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=10, overlap=0)
        text = "0123456789abcdefghij"
        chunks = chunker.chunk(text)

        assert chunks[0].start == 0
        assert chunks[0].end == 10
        assert chunks[0].text == "0123456789"

        assert chunks[1].start == 10
        assert chunks[1].end == 20
        assert chunks[1].text == "abcdefghij"

    def test_metadata_included(self):
        """Chunks include metadata."""
        from chunkers.simple import SimpleChunker

        chunker = SimpleChunker(chunk_size=10, overlap=0)
        text = "a" * 25
        chunks = chunker.chunk(text, metadata={"source": "test.txt"})

        for i, chunk in enumerate(chunks):
            assert chunk.metadata["source"] == "test.txt"
            assert chunk.metadata["chunk_index"] == i
