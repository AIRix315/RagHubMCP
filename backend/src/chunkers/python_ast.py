"""Python AST-based chunker.

This module provides a chunker that uses tree-sitter to parse Python code
and extract semantic units (functions, classes) as chunks.
"""

from __future__ import annotations

import logging
from typing import Any

from .ast_base import ASTChunkerBase

logger = logging.getLogger(__name__)

# Lazy import for tree-sitter Python grammar
_ts_python: Any = None


def _get_tree_sitter_python() -> Any:
    """Lazily import tree-sitter-python.
    
    Returns:
        The tree_sitter_python module
        
    Raises:
        ImportError: If tree-sitter-python is not installed
    """
    global _ts_python
    if _ts_python is None:
        import tree_sitter_python
        _ts_python = tree_sitter_python
    return _ts_python


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
    
    # Tree-sitter query for Python semantic units
    # Matches functions and classes, capturing their names
    QUERY_STRING = """
    (function_definition
        name: (identifier) @name) @chunk
    
    (class_definition
        name: (identifier) @name) @chunk
    """
    
    def get_language(self) -> Any:
        """Get the tree-sitter Language for Python.
        
        Returns:
            The tree-sitter Language object for Python
        """
        ts_python = _get_tree_sitter_python()
        from tree_sitter import Language
        return Language(ts_python.language())
    
    def get_query_string(self) -> str:
        """Get the tree-sitter query string for Python.
        
        Returns:
            Query string matching function and class definitions
        """
        return self.QUERY_STRING
    
    def _extract_name(
        self, 
        captures: dict[str, list[Any]], 
        chunk_node: Any
    ) -> str | None:
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
        
        # For decorated definitions, look for nested function/class
        if chunk_node.type == "decorated_definition":
            for child in chunk_node.children:
                if child.type in ("function_definition", "class_definition"):
                    for subchild in child.children:
                        if subchild.type == "identifier":
                            return subchild.text.decode("utf-8")
        
        return None