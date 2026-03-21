"""Chunker abstraction layer base classes and data structures.

This module defines the foundational components for the chunker system:
- Chunk: Dataclass representing a text chunk with metadata
- ChunkerPlugin: Abstract base class for all chunker implementations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """Represents a text chunk with position and metadata.
    
    Attributes:
        text: The chunk text content
        start: Start position (character offset) in the original document
        end: End position (character offset) in the original document
        metadata: Additional metadata about the chunk (e.g., source file, 
                  heading, language)
    
    Example:
        >>> chunk = Chunk(
        ...     text="Hello world",
        ...     start=0,
        ...     end=11,
        ...     metadata={"source": "test.txt"}
        ... )
    """
    text: str
    start: int
    end: int
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Return the length of the chunk text."""
        return len(self.text)


class ChunkerPlugin(ABC):
    """Abstract base class for all chunker plugins.
    
    A chunker plugin splits text into smaller chunks suitable for
    embedding and retrieval. Each plugin implements a specific
    chunking strategy (e.g., character-based, line-based, semantic).
    
    Class Attributes:
        NAME: Unique identifier for this chunker type
        SUPPORTED_LANGUAGES: List of language identifiers this chunker
                             handles specially (empty = universal)
    
    Instance Attributes:
        chunk_size: Maximum size of each chunk (meaning varies by strategy)
        overlap: Number of characters/lines to overlap between chunks
    
    Example:
        >>> class MyChunker(ChunkerPlugin):
        ...     NAME = "my-chunker"
        ...     
        ...     def chunk(self, text: str) -> list[Chunk]:
        ...         # Implementation
        ...         pass
    """
    
    NAME: str
    SUPPORTED_LANGUAGES: list[str] = []
    
    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> None:
        """Initialize the chunker with size and overlap parameters.
        
        Args:
            chunk_size: Maximum size of each chunk
            overlap: Number of units to overlap between chunks
            
        Raises:
            ValueError: If chunk_size <= 0 or overlap < 0 or overlap >= chunk_size
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if overlap < 0:
            raise ValueError(f"overlap cannot be negative, got {overlap}")
        if overlap >= chunk_size:
            raise ValueError(
                f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
            )
        
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    @abstractmethod
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into chunks.
        
        Args:
            text: The text to split into chunks
            metadata: Optional base metadata to include in each chunk
            
        Returns:
            List of Chunk objects
        """
        ...
    
    def supports_language(self, language: str) -> bool:
        """Check if this chunker has special support for a language.
        
        Args:
            language: Language identifier (e.g., "python", "markdown")
            
        Returns:
            True if the language is in SUPPORTED_LANGUAGES, 
            or if SUPPORTED_LANGUAGES is empty (universal support)
        """
        if not self.SUPPORTED_LANGUAGES:
            return True
        return language.lower() in [lang.lower() for lang in self.SUPPORTED_LANGUAGES]
    
    def _create_metadata(
        self,
        base_metadata: dict[str, Any] | None,
        chunk_index: int,
        **extra: Any
    ) -> dict[str, Any]:
        """Create metadata for a chunk by merging base metadata with extra fields.
        
        Args:
            base_metadata: Optional base metadata to copy from
            chunk_index: Index of the chunk (will be added to metadata)
            **extra: Additional metadata fields to merge
            
        Returns:
            New metadata dictionary with chunk_index and extra fields merged
        """
        result = base_metadata.copy() if base_metadata else {}
        result["chunk_index"] = chunk_index
        result.update(extra)
        return result