"""Line-based chunker.

This module provides a chunker that splits text based on line count,
preserving line boundaries.
"""

from __future__ import annotations

from typing import Any

from .base import Chunk, ChunkerPlugin


class LineChunker(ChunkerPlugin):
    """Line-based text chunker.
    
    Splits text into chunks based on line count. Each chunk contains
    at most `chunk_size` lines. Supports overlap between consecutive
    chunks (in lines).
    
    This chunker is suitable for code files and structured text where
    line boundaries are meaningful.
    
    Attributes:
        NAME: "line"
        chunk_size: Maximum lines per chunk
        overlap: Number of lines to overlap between chunks
    
    Example:
        >>> chunker = LineChunker(chunk_size=10, overlap=2)
        >>> text = "\\n".join([f"Line {i}" for i in range(30)])
        >>> chunks = chunker.chunk(text)
        >>> all(len(c.text.split("\\n")) <= 10 for c in chunks)
        True
    """
    
    NAME = "line"
    
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into line-based chunks.
        
        Args:
            text: The text to split
            metadata: Optional base metadata for each chunk
            
        Returns:
            List of Chunk objects, each containing at most `chunk_size` lines
            
        Note:
            - Empty text returns empty list
            - Line boundaries are preserved
            - The chunk's start/end positions are character offsets
        """
        if not text:
            return []
        
        chunks: list[Chunk] = []
        
        # Find all line boundaries (character positions)
        line_starts = [0]
        for i, char in enumerate(text):
            if char == "\n":
                line_starts.append(i + 1)
        
        # Remove the position after last newline if it's at end of text
        if line_starts and line_starts[-1] == len(text) and text.endswith("\n"):
            line_starts.pop()
        
        # If no newlines, treat entire text as one line
        if len(line_starts) == 1 and "\n" not in text:
            line_starts.append(len(text))
        
        num_lines = len(line_starts)
        step = self.chunk_size - self.overlap
        
        chunk_index = 0
        line_idx = 0
        
        while line_idx < num_lines:
            # Determine the range of lines for this chunk
            end_line_idx = min(line_idx + self.chunk_size, num_lines)
            
            # Get character positions
            start_pos = line_starts[line_idx]
            end_pos = (
                line_starts[end_line_idx] 
                if end_line_idx < num_lines 
                else len(text)
            )
            
            chunk_text = text[start_pos:end_pos]
            
            # Strip trailing newline from chunk text for cleaner output
            # but keep position accurate
            chunks.append(Chunk(
                text=chunk_text,
                start=start_pos,
                end=end_pos,
                metadata=self._create_metadata(
                    metadata, 
                    chunk_index,
                    line_start=line_idx + 1,  # 1-indexed
                    line_end=end_line_idx      # inclusive, 1-indexed
                )
            ))
            
            if end_line_idx >= num_lines:
                break
            
            chunk_index += 1
            line_idx += step
        
        return chunks