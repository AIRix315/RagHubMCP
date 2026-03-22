"""Simple character-based chunker.

This module provides a straightforward chunker that splits text based on
character count, with optional overlap between chunks.
"""

from __future__ import annotations

from typing import Any

from .base import Chunk, ChunkerPlugin


class SimpleChunker(ChunkerPlugin):
    """Character-based text chunker.

    Splits text into chunks of a maximum character count. Each chunk
    will have at most `chunk_size` characters. Supports overlap between
    consecutive chunks.

    This is the default chunker for unknown file types and serves as a
    universal fallback.

    Attributes:
        NAME: "simple"
        chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks

    Example:
        >>> chunker = SimpleChunker(chunk_size=100, overlap=20)
        >>> text = "Hello world! " * 20
        >>> chunks = chunker.chunk(text)
        >>> all(len(c.text) <= 100 for c in chunks)
        True
    """

    NAME = "simple"

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into character-based chunks.

        Args:
            text: The text to split
            metadata: Optional base metadata for each chunk

        Returns:
            List of Chunk objects, each with at most `chunk_size` characters

        Note:
            - Empty text returns empty list
            - Chunks preserve the exact position in original text
            - Overlap is achieved by stepping back by (chunk_size - overlap)
              after each chunk
        """
        if not text:
            return []

        chunks: list[Chunk] = []

        start = 0
        text_len = len(text)
        step = self.chunk_size - self.overlap

        chunk_index = 0
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_text = text[start:end]

            chunks.append(
                Chunk(
                    text=chunk_text,
                    start=start,
                    end=end,
                    metadata=self._create_metadata(metadata, chunk_index),
                )
            )

            chunk_index += 1
            # Move start position, accounting for overlap
            if end == text_len:
                break
            start += step

        return chunks
