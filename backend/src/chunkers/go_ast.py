"""Go AST-based chunker.

This module provides a chunker that uses tree-sitter to parse Go code
and extract semantic units (functions, methods, types) as chunks.
"""

from __future__ import annotations

from typing import Any

from .ast_base import ASTChunkerBase


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
    LANGUAGE_MODULE = "tree_sitter_go"
    LANGUAGE_NAME = "go"
    
    # Tree-sitter query for Go semantic units
    QUERY_STRING = """
    (function_declaration
        name: (identifier) @name) @chunk
    
    (method_declaration
        name: (field_identifier) @name) @chunk
    
    (type_declaration
        (type_spec
            name: (type_identifier) @name)) @chunk
    """
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-register language module when subclass is defined."""
        super().__init_subclass__(**kwargs)
        cls.auto_register()
    
    def _extract_name(self, captures: dict[str, list[Any]], chunk_node: Any) -> str | None:
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
        
        # For type_declaration or other complex nodes, recursively search for identifier
        return self._find_name_in_children(chunk_node, ["type_identifier", "field_identifier", "identifier"])