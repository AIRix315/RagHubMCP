"""TypeScript AST-based chunker.

This module provides a chunker that uses tree-sitter to parse TypeScript/TSX code
and extract semantic units (functions, classes, methods) as chunks.
"""

from __future__ import annotations

from typing import Any

from .ast_base import ASTChunkerBase


class TypeScriptASTChunker(ASTChunkerBase):
    """AST-based chunker for TypeScript and TSX code.

    Splits TypeScript/TSX source code into semantic chunks based on
    function declarations, class declarations, and methods. Handles
    both TypeScript (.ts) and TSX (.tsx) files.

    Attributes:
        NAME: "typescript-ast"
        SUPPORTED_LANGUAGES: ["typescript", "ts", "tsx"]

    Example:
        >>> chunker = TypeScriptASTChunker()
        >>> code = '''
        ... function hello(): void {
        ...     console.log("Hello");
        ... }
        ...
        ... class MyClass {
        ...     method(): void {}
        ... }
        ... '''
        >>> chunks = chunker.chunk(code)
        >>> len(chunks)  # 2 chunks: function and class
        2
    """

    NAME = "typescript-ast"
    SUPPORTED_LANGUAGES = ["typescript", "ts", "tsx"]
    LANGUAGE_MODULE = "tree_sitter_typescript"
    LANGUAGE_NAME = "typescript"

    # Tree-sitter query for TypeScript semantic units
    QUERY_STRING = """
    (function_declaration
        name: (identifier) @name) @chunk

    (class_declaration
        name: (type_identifier) @name) @chunk

    (method_definition
        name: (property_identifier) @name) @chunk

    (lexical_declaration
        (variable_declarator
            name: (identifier) @name
            value: (arrow_function))) @chunk

    (lexical_declaration
        (variable_declarator
            name: (identifier) @name
            value: (function_expression))) @chunk
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-register language module when subclass is defined."""
        super().__init_subclass__(**kwargs)
        cls.auto_register()

    def __init__(self, chunk_size: int = 500, overlap: int = 50, *, tsx_mode: bool = False) -> None:
        """Initialize the TypeScript chunker.

        Args:
            chunk_size: Maximum size hint (preserved for API compatibility)
            overlap: Overlap hint (preserved for API compatibility)
            tsx_mode: If True, use TSX grammar instead of TypeScript
        """
        super().__init__(chunk_size=chunk_size, overlap=overlap)
        self.tsx_mode = tsx_mode

    def get_language(self) -> Any:
        """Get the tree-sitter Language for TypeScript/TSX.

        Returns:
            The tree-sitter Language object for TypeScript or TSX
        """
        language_module = self._load_language_module()
        from tree_sitter import Language

        if self.tsx_mode:
            return Language(language_module.language_tsx())
        return Language(language_module.language_typescript())

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Any]:
        """Split TypeScript code into AST-based chunks.

        Auto-detects TSX mode based on file extension in metadata.

        Args:
            text: TypeScript/TSX source code to split
            metadata: Optional metadata (may contain 'source' or 'file_extension')

        Returns:
            List of Chunk objects
        """
        # Auto-detect TSX mode from metadata
        if metadata and not self.tsx_mode:
            source = metadata.get("source", "")
            if source.endswith(".tsx"):
                self.tsx_mode = True

        return super().chunk(text, metadata)

    def _extract_name(self, captures: dict[str, list[Any]], chunk_node: Any) -> str | None:
        """Extract the name for a TypeScript chunk node.

        Handles various TypeScript node types including arrow functions
        stored in variables.

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

        # For lexical_declaration with arrow function, get the variable name
        return self._find_name_in_children(chunk_node, "identifier")
