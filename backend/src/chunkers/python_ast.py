"""Python AST-based chunker.

This module provides a chunker that uses tree-sitter to parse Python code
and extract semantic units (functions, classes) as chunks.
"""

from __future__ import annotations

from typing import Any

from .ast_base import ASTChunkerBase


class PythonASTChunker(ASTChunkerBase):
    """AST-based chunker for Python code.
    
    Splits Python source code into semantic chunks based on function
    and class definitions. Preserves the complete structure of each
    definition including decorators, docstrings, and body.
    
    Attributes:
        NAME: "python-ast"
        SUPPORTED_LANGUAGES: ["python", "py"]
        
    Example:
        >>> chunker = PythonASTChunker()
        >>> code = '''
        ... def hello():
        ...     print("Hello")
        ... 
        ... class MyClass:
        ...     def method(self):
        ...         pass
        ... '''
        >>> chunks = chunker.chunk(code)
        >>> len(chunks)  # 2 chunks: function and class
        2
    """
    
    NAME = "python-ast"
    SUPPORTED_LANGUAGES = ["python", "py"]
    LANGUAGE_MODULE = "tree_sitter_python"
    LANGUAGE_NAME = "python"
    
    # Tree-sitter query for Python semantic units
    QUERY_STRING = """
    (function_definition
        name: (identifier) @name) @chunk
    
    (class_definition
        name: (identifier) @name) @chunk
    """
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-register language module when subclass is defined."""
        super().__init_subclass__(**kwargs)
        cls.auto_register()
    
    def _extract_name(self, captures: dict[str, list[Any]], chunk_node: Any) -> str | None:
        """Extract the name for a Python chunk node.
        
        Handles decorated definitions by finding the actual function/class name.
        
        Args:
            captures: Dictionary of capture name -> list of nodes
            chunk_node: The node being chunked
            
        Returns:
            The extracted function/class name or None
        """
        # First try the standard approach
        name = super()._extract_name(captures, chunk_node)
        if name:
            return name
        
        # For decorated definitions or other complex nodes, recursively search for identifier
        return self._find_name_in_children(chunk_node, "identifier")