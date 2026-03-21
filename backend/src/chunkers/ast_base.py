"""Abstract base class for AST-based chunkers.

This module provides the foundation for language-specific AST chunkers
using tree-sitter for parsing and querying code structures.

Classes:
    ASTChunkerBase: Abstract base class for AST-based chunking

Language Support:
    - Python: python_ast.py
    - TypeScript/TSX: typescript_ast.py
    - Go: go_ast.py
"""

from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .base import Chunk, ChunkerPlugin

logger = logging.getLogger(__name__)

# Type imports for type checking only
if TYPE_CHECKING:
    pass

# Try to import tree-sitter, gracefully degrade if not available
_TREE_SITTER_AVAILABLE = False
_language: type | None = None
_parser: type | None = None
_query: type | None = None
_query_cursor: type | None = None
try:
    from tree_sitter import Language as _language  # noqa: N813, F401
    from tree_sitter import Parser as _parser  # noqa: N813, F401
    from tree_sitter import Query as _query  # noqa: N813, F401
    from tree_sitter import QueryCursor as _query_cursor  # noqa: N813, F401

    _TREE_SITTER_AVAILABLE = True
except ImportError:
    pass

# Registry for tree-sitter language modules
# Maps language name to lazy loader function
_LANGUAGE_REGISTRY: dict[str, Callable[[], Any]] = {}
_LANGUAGE_CACHE: dict[str, Any] = {}


def register_language(name: str, loader: Callable[[], Any]) -> None:
    """Register a tree-sitter language module loader.

    Args:
        name: Language identifier (e.g., 'python', 'typescript', 'go')
        loader: Function that imports and returns the language module
    """
    _LANGUAGE_REGISTRY[name] = loader


def get_language_module(name: str) -> Any:
    """Get a tree-sitter language module (lazy loaded and cached).

    Args:
        name: Language identifier

    Returns:
        The tree-sitter language module

    Raises:
        ImportError: If the language module is not installed
    """
    if name in _LANGUAGE_CACHE:
        return _LANGUAGE_CACHE[name]

    if name not in _LANGUAGE_REGISTRY:
        raise ImportError(f"Language '{name}' is not registered")

    module = _LANGUAGE_REGISTRY[name]()
    _LANGUAGE_CACHE[name] = module
    return module


def make_language_loader(module_name: str) -> Callable[[], Any]:
    """Create a lazy language loader function.

    Factory function to reduce boilerplate in subclass files.

    Args:
        module_name: Name of the tree-sitter module (e.g., 'tree_sitter_python')

    Returns:
        A function that imports and returns the language module

    Example:
        >>> register_language("python", make_language_loader("tree_sitter_python"))
    """

    def loader() -> Any:
        module = __import__(module_name)
        return module

    return loader


class ASTChunkerBase(ChunkerPlugin, ABC):
    """Abstract base class for AST-based code chunkers.

    Uses tree-sitter to parse source code and extract semantic units
    (functions, classes, methods) as chunks.

    Subclasses must implement:
        - LANGUAGE_MODULE: Module name for tree-sitter language (e.g., 'tree_sitter_python')
        - LANGUAGE_NAME: Language identifier for registry (e.g., 'python')
        - QUERY_STRING: Tree-sitter query string for finding chunks
    OPTIONAL:
        - _extract_name(): Override for custom name extraction logic

    Attributes:
        NAME: Chunker name (to be set by subclass)
        SUPPORTED_LANGUAGES: List of supported language identifiers
        chunk_size: Maximum size hint (AST chunks preserve semantic units)
        overlap: Overlap hint (not used for AST chunking)
    """

    # Subclasses must override these
    NAME: str = "ast-base"
    SUPPORTED_LANGUAGES: list[str] = []

    # Language module and identifier (subclasses must set)
    LANGUAGE_MODULE: str = ""  # e.g., 'tree_sitter_python'
    LANGUAGE_NAME: str = ""  # e.g., 'python'

    # Query string - subclasses MUST override
    QUERY_STRING: str = ""

    @classmethod
    def is_tree_sitter_available(cls) -> bool:
        """Check if tree-sitter is available.

        Returns:
            True if tree-sitter is installed and importable
        """
        return _TREE_SITTER_AVAILABLE

    @classmethod
    def auto_register(cls) -> None:
        """Auto-register this chunker's language module.

        Convenience method to reduce boilerplate. Uses LANGUAGE_MODULE
        and LANGUAGE_NAME from the subclass to create and register
        a lazy loader.

        Example:
            >>> class PythonASTChunker(ASTChunkerBase):
            ...     LANGUAGE_MODULE = "tree_sitter_python"
            ...     LANGUAGE_NAME = "python"
            ...     PythonASTChunker.auto_register()
        """
        if not cls.LANGUAGE_MODULE or not cls.LANGUAGE_NAME:
            raise ValueError(
                f"Subclass {cls.__name__} must define LANGUAGE_MODULE and LANGUAGE_NAME"
            )
        register_language(cls.LANGUAGE_NAME, make_language_loader(cls.LANGUAGE_MODULE))

    @classmethod
    def _load_language_module(cls) -> Any:
        """Load the tree-sitter language module for this chunker.

        Uses the registry for lazy loading and caching.

        Returns:
            The tree-sitter language module

        Raises:
            ImportError: If the language module is not installed
        """
        if not cls.LANGUAGE_MODULE or not cls.LANGUAGE_NAME:
            raise ValueError(
                f"Subclass {cls.__name__} must define LANGUAGE_MODULE and LANGUAGE_NAME"
            )

        # Try to get from registry first
        if cls.LANGUAGE_NAME in _LANGUAGE_REGISTRY:
            return get_language_module(cls.LANGUAGE_NAME)

        # If not registered, attempt direct import
        module = __import__(cls.LANGUAGE_MODULE)
        _LANGUAGE_CACHE[cls.LANGUAGE_NAME] = module
        return module

    def get_language(self) -> Any:
        """Get the tree-sitter Language for this chunker.

        Default implementation uses LANGUAGE_MODULE and LANGUAGE_NAME.
        Subclasses can override for custom behavior (e.g., TSX vs TypeScript).

        Returns:
            The tree-sitter Language object for the specific language
        """
        language_module = self._load_language_module()

        # Most tree-sitter modules have a language() function
        if hasattr(language_module, "language"):
            lang_func = getattr(language_module, "language")
            from tree_sitter import Language

            return Language(lang_func())

        raise NotImplementedError(
            f"Subclass {self.__class__.__name__} must implement get_language() "
            f"or ensure {self.LANGUAGE_MODULE}.language() is available"
        )

    def get_query_string(self) -> str:
        """Get the tree-sitter query string for finding chunks.

        Returns:
            A tree-sitter query string that matches nodes to chunk
        """
        if not self.QUERY_STRING:
            raise ValueError(f"Subclass {self.__name__} must define QUERY_STRING")
        return self.QUERY_STRING

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

        if (
            not self.is_tree_sitter_available()
            or _parser is None
            or _query is None
            or _query_cursor is None
        ):
            logger.warning(
                "tree-sitter is not installed. AST chunking is unavailable. "
                "Install with: pip install raghub-mcp[ast]"
            )
            return []

        base_metadata = metadata.copy() if metadata else {}

        try:
            language = self.get_language()
            parser = _parser(language)
            tree = parser.parse(bytes(text, "utf-8"))
            root_node = tree.root_node

            query_string = self.get_query_string()
            query = _query(language, query_string)
            cursor = _query_cursor(query)
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

                chunks.append(
                    Chunk(
                        text=chunk_text,
                        start=node.start_byte,
                        end=node.end_byte,
                        metadata=chunk_metadata,
                    )
                )

            # If no chunks found but file has content, return single chunk
            if not chunks and text.strip():
                logger.debug("No AST nodes found for chunking, returning single chunk")
                chunks.append(
                    Chunk(
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
                    )
                )

            return chunks

        except Exception as e:
            logger.warning(f"AST parsing failed: {e}. Returning single chunk.")
            return [
                Chunk(
                    text=text,
                    start=0,
                    end=len(text),
                    metadata={
                        **base_metadata,
                        "chunk_index": 0,
                        "node_type": "parse_error",
                        "error": str(e),
                    },
                )
            ]

    def _extract_name(self, captures: dict[str, list[Any]], chunk_node: Any) -> str | None:
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
            if (
                name_node.start_byte >= chunk_node.start_byte
                and name_node.end_byte <= chunk_node.end_byte
            ):
                return name_node.text.decode("utf-8")
        return None

    def _find_name_in_children(self, node: Any, target_types: list[str] | str) -> str | None:
        """Recursively search for an identifier node in children.

        Helper method to reduce boilerplate in _extract_name implementations.
        Searches through node children to find a node of the specified type(s)
        and returns its text content.

        Args:
            node: The tree-sitter node to search
            target_types: Single type string or list of type strings to match
                         (e.g., 'identifier', ['identifier', 'type_identifier'])

        Returns:
            The text content of the first matching node, or None if not found

        Example:
            >>> name = self._find_name_in_children(chunk_node, 'identifier')
            >>> name = self._find_name_in_children(node, ['identifier', 'type_identifier'])
        """
        if isinstance(target_types, str):
            target_types = [target_types]

        for child in node.children:
            if child.type in target_types:
                return child.text.decode("utf-8")

        # Recursively search deeper if direct children don't match
        for child in node.children:
            result = self._find_name_in_children(child, target_types)
            if result:
                return result

        return None
