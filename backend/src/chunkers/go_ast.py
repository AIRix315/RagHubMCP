"""Go AST-based chunker.

This module provides a chunker that uses tree-sitter to parse Go code
and extract semantic units (functions, methods, types) as chunks.
"""

from __future__ import annotations

import logging
from typing import Any

from .ast_base import ASTChunkerBase

logger = logging.getLogger(__name__)

# Lazy import for tree-sitter Go grammar
_ts_go: Any = None


def _get_tree_sitter_go() -> Any:
    """Lazily import tree-sitter-go.
    
    Returns:
        The tree_sitter_go module
        
    Raises:
        ImportError: If tree-sitter-go is not installed
    """
    global _ts_go
    if _ts_go is None:
        import tree_sitter_go
        _ts_go = tree_sitter_go
    return _ts_go


class GoASTChunker(ASTChunkerBase):
    """AST-based chunker for Go code.
    
    Splits Go source code into semantic chunks based on function
    declarations, method declarations, and type declarations.
    
    Attributes:
        NAME: "go-ast"
        SUPPORTED_LANGUAGES: ["go", "golang"]
        
    Example:
        >>> chunker = GoASTChunker()
        >>> code = '''
        ... package main
        ... 
        ... func hello() {
        ...     fmt.Println("Hello")
        ... }
        ... 
        ... type MyStruct struct {
        ...     Field string
        ... }
        ... '''
        >>> chunks = chunker.chunk(code)
        >>> len(chunks)  # 2 chunks: function and type
        2
    """
    
    NAME = "go-ast"
    SUPPORTED_LANGUAGES = ["go", "golang"]
    
    # Tree-sitter query for Go semantic units
    # Matches functions, methods, and type declarations
    QUERY_STRING = """
    (function_declaration
        name: (identifier) @name) @chunk
    
    (method_declaration
        name: (field_identifier) @name) @chunk
    
    (type_declaration
        (type_spec
            name: (type_identifier) @name)) @chunk
    """
    
    def get_language(self) -> Any:
        """Get the tree-sitter Language for Go.
        
        Returns:
            The tree-sitter Language object for Go
        """
        ts_go = _get_tree_sitter_go()
        from tree_sitter import Language
        return Language(ts_go.language())
    
    def get_query_string(self) -> str:
        """Get the tree-sitter query string for Go.
        
        Returns:
            Query string matching functions, methods, and types
        """
        return self.QUERY_STRING
    
    def _extract_name(
        self, 
        captures: dict[str, list[Any]], 
        chunk_node: Any
    ) -> str | None:
        """Extract the name for a Go chunk node.
        
        Handles Go-specific node types including method receivers
        and type declarations.
        
        Args:
            captures: Dictionary of capture name -> list of nodes
            chunk_node: The node being chunked
            
        Returns:
            The extracted name or None
        """
        # Standard name extraction
        name = super()._extract_name(captures, chunk_node)
        if name:
            return name
        
        # For type_declaration, find the type_spec's name
        if chunk_node.type == "type_declaration":
            for child in chunk_node.children:
                if child.type == "type_spec":
                    for subchild in child.children:
                        if subchild.type == "type_identifier":
                            return subchild.text.decode("utf-8")
        
        return None