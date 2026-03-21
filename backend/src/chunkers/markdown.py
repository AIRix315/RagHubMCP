"""Markdown-aware chunker.

This module provides a chunker that splits Markdown documents based on
heading structure, keeping sections together.
"""

from __future__ import annotations

import re
from typing import Any

from .base import Chunk, ChunkerPlugin


class MarkdownChunker(ChunkerPlugin):
    """Markdown-aware text chunker.
    
    Splits Markdown documents based on heading structure. Each section
    (content under a heading) becomes a potential chunk. If a section
    exceeds `chunk_size` characters, it falls back to character-based
    splitting for that section.
    
    Headings are detected using the standard Markdown syntax:
    - ATX style: # Heading 1, ## Heading 2, etc.
    - Setext style: Underlined with === or ---
    
    Attributes:
        NAME: "markdown"
        SUPPORTED_LANGUAGES: ["markdown", "md"]
        chunk_size: Maximum characters per chunk
        overlap: Overlap for fallback character splitting
    
    Example:
        >>> chunker = MarkdownChunker(chunk_size=500)
        >>> text = "# Title\\n\\nContent here.\\n\\n## Section\\n\\nMore content."
        >>> chunks = chunker.chunk(text)
        >>> # Each chunk corresponds to a section
    """
    
    NAME = "markdown"
    SUPPORTED_LANGUAGES = ["markdown", "md"]
    
    # Regex patterns for Markdown headings
    # ATX style: # Heading (1-6 hashes)
    ATX_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", re.MULTILINE)
    
    # Setext style: Heading text followed by === or --- on next line
    SETEXT_HEADING_PATTERN = re.compile(
        r"^(.+?)\n([=-]{3,})$",
        re.MULTILINE
    )
    
    def _find_headings(self, text: str) -> list[tuple[int, int, str, int]]:
        """Find all headings in the text.
        
        Returns:
            List of (start_pos, end_pos, heading_text, level) tuples
        """
        headings = []
        
        # Find ATX-style headings
        for match in self.ATX_HEADING_PATTERN.finditer(text):
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append((match.start(), match.end(), heading_text, level))
        
        # Find Setext-style headings
        for match in self.SETEXT_HEADING_PATTERN.finditer(text):
            heading_text = match.group(1).strip()
            underline = match.group(2)
            level = 1 if underline[0] == "=" else 2
            headings.append((match.start(), match.end(), heading_text, level))
        
        # Sort by position
        headings.sort(key=lambda x: x[0])
        
        return headings
    
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split Markdown text into section-based chunks.
        
        Args:
            text: The Markdown text to split
            metadata: Optional base metadata for each chunk
            
        Returns:
            List of Chunk objects, each representing a section
            
        Note:
            - Document title (first heading) is included in metadata
            - Each chunk contains the heading and its content
            - Large sections are split using character-based fallback
        """
        if not text:
            return []
        
        chunks: list[Chunk] = []
        
        headings = self._find_headings(text)
        
        # No headings: treat entire document as one chunk
        if not headings:
            if len(text) <= self.chunk_size:
                return [Chunk(
                    text=text,
                    start=0,
                    end=len(text),
                    metadata=self._create_metadata(metadata, 0)
                )]
            # Fall back to character-based splitting
            return self._split_large_section(text, 0, metadata)
        
        # Process each section (from heading to next heading or end)
        for i, (start, end, heading_text, level) in enumerate(headings):
            # Determine section end
            if i + 1 < len(headings):
                section_end = headings[i + 1][0]
            else:
                section_end = len(text)
            
            section_text = text[start:section_end]
            
            # Check if section is too large
            if len(section_text) > self.chunk_size:
                # Split large section, preserving heading
                section_chunks = self._split_large_section(
                    section_text, start, metadata, heading_text
                )
                chunks.extend(section_chunks)
            else:
                chunks.append(Chunk(
                    text=section_text,
                    start=start,
                    end=section_end,
                    metadata=self._create_metadata(
                        metadata,
                        len(chunks),
                        heading=heading_text,
                        heading_level=level
                    )
                ))
        
        return chunks
    
    def _split_large_section(
        self,
        text: str,
        offset: int,
        base_metadata: dict[str, Any] | None,
        heading: str | None = None
    ) -> list[Chunk]:
        """Split a large section using character-based fallback.
        
        Args:
            text: The section text to split
            offset: Character offset in original document
            base_metadata: Base metadata for chunks (can be None)
            heading: Optional heading text for metadata
            
        Returns:
            List of Chunk objects
        """
        chunks: list[Chunk] = []
        text_len = len(text)
        step = self.chunk_size - self.overlap
        start = 0
        chunk_idx = 0
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_text = text[start:end]
            
            chunk_metadata = self._create_metadata(
                base_metadata,
                chunk_idx,
                large_section=True
            )
            if heading:
                chunk_metadata["heading"] = heading
            
            chunks.append(Chunk(
                text=chunk_text,
                start=offset + start,
                end=offset + end,
                metadata=chunk_metadata
            ))
            
            if end == text_len:
                break
            
            chunk_idx += 1
            start += step
        
        return chunks