"""Abstract base class for AST-based chunkers.

This module provides the foundation for language-specific AST chunkers
using tree-sitter for parsing and querying code structures.

Classes:
    ASTChunkerBase: Abstract base class for AST-based chunking
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .base import Chunk, ChunkerPlugin

logger = logging.getLogger(__name__)

# Type imports for type checking only
if TYPE_CHECKING:
    from tree_sitter import Language, Node, Parser, Query, QueryCursor

# Try to import tree-sitter, gracefully degrade if not available
_TREE_SITTER_AVAILABLE = False
_LANGUAGE: type | None = None
_PARSER: type | None = None
_QUERY: type | None = None
_QUERY_CURSOR: type | None = None
try:
    from tree_sitter import Language as _LANGUAGE
    from tree_sitter import Parser as _PARSER
    from tree_sitter import Query as _QUERY
    from tree_sitter import QueryCursor as _QUERY_CURSOR
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    pass


class ASTChunkerBase(ChunkerPlugin, ABC):
    """Abstract base class for AST-based code chunkers.
    
    Uses tree-sitter to parse source code and extract semantic units
    (functions, classes, methods) as chunks.
    
    Subclasses must implement:
        - get_language(): Return the tree-sitter Language object
        - get_query_string(): Return the tree-sitter query string
        
    Attributes:
        NAME: Chunker name (to be set by subclass)
        SUPPORTED_LANGUAGES: List of supported language identifiers
        chunk_size: Maximum size hint (AST chunks preserve semantic units)
        overlap: Overlap hint (not used for AST chunking)
    """
    
    # Subclasses should override these
    NAME: str = "ast-base"
    SUPPORTED_LANGUAGES: list[str] = []
    
    @classmethod
    def is_tree_sitter_available(cls) -> bool:
        """Check if tree-sitter is available.
        
        Returns:
            True if tree-sitter is installed and importable
        """
        return _TREE_SITTER_AVAILABLE
    
    @abstractmethod
    def get_language(self) -> Any:
        """Get the tree-sitter Language for this chunker.
        
        Returns:
            The tree-sitter Language object for the specific language
            
        Example:
            >>> import tree_sitter_python
            >>> return Language(tree_sitter_python.language())
        """
        ...
    
    @abstractmethod
    def get_query_string(self) -> str:
        """Get the tree-sitter query string for finding chunks.
        
        Returns:
            A tree-sitter query string that matches nodes to chunk
            
        Example:
            >>> return \"\"\"
            ... (function_definition name: (identifier) @name) @chunk
            ... (class_definition name: (identifier) @name) @chunk
            ... \"\"\"
        """
        ...
    
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split code into AST-based semantic chunks.
        
        Args:
            text: Source code to split
            metadata: Optional base metadata for each chunk
            
        Returns:
            List of Chunk objects representing functions, classes, etc.
            
        Note:
            - Returns empty list if tree-sitter is not available
            - Returns single chunk with full text if parsing fails
            - Preserves semantic boundaries (won't split mid-function)
        """
        if not text or not text.strip():
            return []
        
        if not self.is_tree_sitter_available() or _PARSER is None or _QUERY is None or _QUERY_CURSOR is None:
            logger.warning(
                "tree-sitter is not installed. AST chunking is unavailable. "
                "Install with: pip install raghub-mcp[ast]"
            )
            return []
        
        base_metadata = metadata.copy() if metadata else {}
        
        try:
            language = self.get_language()
            parser = _PARSER(language)
            tree = parser.parse(bytes(text, "utf-8"))
            root_node = tree.root_node
            
            query_string = self.get_query_string()
            query = _QUERY(language, query_string)
            cursor = _QUERY_CURSOR(query)
            captures = cursor.captures(root_node)
            
            chunks: list[Chunk] = []
            chunk_nodes = captures.get("chunk", [])
            
            for node in chunk_nodes:
                chunk_text = node.text.decode("utf-8")
                if not chunk_text.strip():
                    continue
                    
                # Extract name from capture if available
                name = self._extract_name(captures, node)
                
                # Build chunk metadata
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": len(chunks),
                    "node_type": node.type,
                    "start_line": node.start_point[0] + 1,  # 1-indexed
                    "end_line": node.end_point[0] + 1,
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte,
                }
                
                if name:
                    chunk_metadata["name"] = name
                
                chunks.append(Chunk(
                    text=chunk_text,
                    start=node.start_byte,
                    end=node.end_byte,
                    metadata=chunk_metadata,
                ))
            
            # If no chunks found but file has content, return single chunk
            if not chunks and text.strip():
                logger.debug(
                    "No AST nodes found for chunking, returning single chunk"
                )
                chunks.append(Chunk(
                    text=text,
                    start=0,
                    end=len(text),
                    metadata={
                        **base_metadata,
                        "chunk_index": 0,
                        "node_type": "source_file",
                        "start_line": 1,
                        "end_line": text.count("\n") + 1,
                    },
                ))
            
            return chunks
            
        except Exception as e:
            logger.warning(f"AST parsing failed: {e}. Returning single chunk.")
            return [Chunk(
                text=text,
                start=0,
                end=len(text),
                metadata={
                    **base_metadata,
                    "chunk_index": 0,
                    "node_type": "parse_error",
                    "error": str(e),
                },
            )]
    
    def _extract_name(
        self, 
        captures: dict[str, list[Any]], 
        chunk_node: Any
    ) -> str | None:
        """Extract the name for a chunk node.
        
        Looks for a 'name' capture that corresponds to the chunk node.
        Subclasses can override for more complex name extraction.
        
        Args:
            captures: Dictionary of capture name -> list of nodes
            chunk_node: The node being chunked
            
        Returns:
            The extracted name or None
        """
        name_nodes = captures.get("name", [])
        for name_node in name_nodes:
            # Check if name node is within the chunk node
            if (name_node.start_byte >= chunk_node.start_byte and
                name_node.end_byte <= chunk_node.end_byte):
                return name_node.text.decode("utf-8")
        return None