"""Tests for MarkdownChunker.

Test cases:
- TC-1.9.4: MarkdownChunker 按标题切分
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestMarkdownChunker:
    """TC-1.9.4: MarkdownChunker 按标题切分"""

    def test_splits_by_headings(self):
        """TC-1.9.4: Text is split at heading boundaries."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        
        text = """# Title

This is the intro content.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
        chunks = chunker.chunk(text)
        
        # Should have 3 chunks: title section, section 1, section 2
        assert len(chunks) == 3
        
        # First chunk contains title
        assert "# Title" in chunks[0].text
        
        # Second chunk contains Section 1
        assert "## Section 1" in chunks[1].text
        
        # Third chunk contains Section 2
        assert "## Section 2" in chunks[2].text

    def test_heading_metadata(self):
        """TC-1.9.4: Chunks include heading metadata."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        
        text = """# Main Title

Intro content.

## Subsection

Subsection content.
"""
        chunks = chunker.chunk(text)
        
        assert chunks[0].metadata["heading"] == "Main Title"
        assert chunks[0].metadata["heading_level"] == 1
        
        assert chunks[1].metadata["heading"] == "Subsection"
        assert chunks[1].metadata["heading_level"] == 2

    def test_no_headings_single_chunk(self):
        """Text without headings returns single chunk."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        
        text = "Just some plain text without any headings."
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_empty_text_returns_empty_list(self):
        """Empty text returns empty chunk list."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk("")
        
        assert chunks == []

    def test_atx_headings_level_1_to_6(self):
        """TC-1.9.4: ATX-style headings (1-6 #) are recognized."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        
        text = """# H1
Content 1
## H2
Content 2
### H3
Content 3
#### H4
Content 4
##### H5
Content 5
###### H6
Content 6
"""
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 6
        
        levels = [c.metadata["heading_level"] for c in chunks]
        assert levels == [1, 2, 3, 4, 5, 6]

    def test_large_section_split(self):
        """Large sections are split using fallback."""
        from chunkers.markdown import MarkdownChunker
        
        # Small chunk size to trigger fallback
        chunker = MarkdownChunker(chunk_size=50, overlap=10)
        
        text = """# Large Section

""" + "This is content. " * 20  # Large content
        
        chunks = chunker.chunk(text)
        
        # Should be split into multiple chunks due to size
        assert len(chunks) >= 1
        
        # All chunks should be within size limit (approximately)
        for chunk in chunks:
            # Allow some flexibility for heading
            assert len(chunk.text) <= chunker.chunk_size + 20

    def test_supports_language_check(self):
        """MarkdownChunker supports markdown and md languages."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=100, overlap=10)
        
        assert chunker.supports_language("markdown") is True
        assert chunker.supports_language("md") is True
        assert chunker.supports_language("MARKDOWN") is True  # case-insensitive
        assert chunker.supports_language("python") is False

    def test_positions_accurate(self):
        """TC-1.9.4: Chunk positions are accurate."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        
        text = """# Title

Content.

## Section

More content.
"""
        chunks = chunker.chunk(text)
        
        for chunk in chunks:
            extracted = text[chunk.start:chunk.end]
            assert extracted == chunk.text

    def test_consecutive_headings(self):
        """Consecutive headings create empty sections."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500, overlap=50)
        
        text = """# Title

## Section

Content here.
"""
        chunks = chunker.chunk(text)
        
        # Title section (empty, just heading)
        assert "# Title" in chunks[0].text
        
        # Section with content
        assert "## Section" in chunks[1].text
        assert "Content here." in chunks[1].text