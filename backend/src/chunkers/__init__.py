"""Chunkers module for text splitting and document chunking.

This module provides a plugin-based chunking system for splitting text
into smaller pieces suitable for embedding and retrieval.

Available chunkers:
- SimpleChunker: Character-based splitting (default, universal)
- LineChunker: Line-based splitting (good for code)
- MarkdownChunker: Section-based splitting (for Markdown files)

Usage:
    from chunkers import registry, SimpleChunker
    
    # Get chunker by name
    chunker_cls = registry.get("simple")
    chunker = chunker_cls(chunk_size=500, overlap=50)
    chunks = chunker.chunk(text)
    
    # Get chunker for a language
    chunker_cls = registry.get_for_language("markdown")
    chunker = chunker_cls(chunk_size=500, overlap=50)
    chunks = chunker.chunk(markdown_text)
"""

from .base import Chunk, ChunkerPlugin
from .simple import SimpleChunker
from .line import LineChunker
from .markdown import MarkdownChunker
from .registry import registry, ChunkerRegistry

__all__ = [
    "Chunk",
    "ChunkerPlugin",
    "SimpleChunker",
    "LineChunker",
    "MarkdownChunker",
    "ChunkerRegistry",
    "registry",
]