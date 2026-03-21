"""Chunkers module for text splitting and document chunking.

This module provides a plugin-based chunking system for splitting text
into smaller pieces suitable for embedding and retrieval.

Available chunkers:
- SimpleChunker: Character-based splitting (default, universal)
- LineChunker: Line-based splitting (good for code)
- MarkdownChunker: Section-based splitting (for Markdown files)

AST-based chunkers (requires `pip install raghub-mcp[ast]`):
- PythonASTChunker: Python AST-based splitting
- TypeScriptASTChunker: TypeScript/TSX AST-based splitting
- GoASTChunker: Go AST-based splitting

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

    # Use AST chunker for Python
    chunker_cls = registry.get("python-ast")
    chunker = chunker_cls()
    chunks = chunker.chunk(python_code)
"""

from .ast_base import ASTChunkerBase
from .base import Chunk, ChunkerPlugin
from .line import LineChunker
from .markdown import MarkdownChunker
from .registry import ChunkerRegistry, registry
from .simple import SimpleChunker

# Lazy imports for AST chunkers (require tree-sitter)
__all__ = [
    "Chunk",
    "ChunkerPlugin",
    "SimpleChunker",
    "LineChunker",
    "MarkdownChunker",
    "ASTChunkerBase",
    "ChunkerRegistry",
    "registry",
    # AST chunkers (lazy loaded)
    "PythonASTChunker",
    "TypeScriptASTChunker",
    "GoASTChunker",
]


def __getattr__(name: str):
    """Lazy import for AST chunkers.

    This allows importing AST chunkers without requiring tree-sitter
    to be installed until the chunker is actually used.
    """
    if name == "PythonASTChunker":
        from .python_ast import PythonASTChunker

        return PythonASTChunker
    elif name == "TypeScriptASTChunker":
        from .typescript_ast import TypeScriptASTChunker

        return TypeScriptASTChunker
    elif name == "GoASTChunker":
        from .go_ast import GoASTChunker

        return GoASTChunker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
