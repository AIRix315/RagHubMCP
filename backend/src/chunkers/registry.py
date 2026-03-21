"""Chunker registry for dynamic registration and lookup.

This module implements the registry pattern for chunker management:
- ChunkerRegistry: Singleton registry for chunker classes
- Decorator-based registration
- Language-aware chunker selection
"""

from __future__ import annotations

from collections.abc import Callable

from src.common.registry import Registry

from .base import ChunkerPlugin


class ChunkerRegistry(Registry[ChunkerPlugin, str]):
    """Chunker registry with singleton pattern.

    Provides a central registration point for all chunker types.
    Supports decorator-based registration and language-aware selection.

    The registry maintains:
    - A name -> chunker_class mapping for explicit lookup
    - A language -> chunker_class mapping for automatic selection

    Example:
        from chunkers.registry import registry

        @registry.register("my-chunker")
        class MyChunker(ChunkerPlugin):
            NAME = "my-chunker"
            ...

        # Later, retrieve the chunker class
        chunker_cls = registry.get("my-chunker")

        # Or get the appropriate chunker for a language
        chunker_cls = registry.get_for_language("markdown")
    """

    _language_map: dict[str, type[ChunkerPlugin]]

    def __init__(self) -> None:
        """Initialize chunker registry."""
        super().__init__()
        # Initialize language_map on first instantiation
        if not hasattr(self, "_language_map"):
            self._language_map = {}
        if not hasattr(self, "_items"):
            self._items = {}

    def register(self, name: str) -> Callable[[type], type]:
        """Decorator to register a chunker class.

        Args:
            name: Unique name for this chunker type (e.g., "simple", "markdown")

        Returns:
            Decorator function that registers the class

        Raises:
            ValueError: If chunker name is already registered

        Example:
            @registry.register("my-chunker")
            class MyChunker(ChunkerPlugin):
                NAME = "my-chunker"
                ...
        """

        def decorator(cls: type) -> type:
            # Use "chunkers" as the fixed key for all chunker registrations
            key = "chunkers"
            if key not in self._items:
                self._items[key] = {}
            if name in self._items[key]:
                raise ValueError(
                    f"Chunker '{name}' already registered. Existing: {self._items[key][name]}"
                )
            self._items[key][name] = cls

            # Build language mapping from SUPPORTED_LANGUAGES
            if hasattr(cls, "SUPPORTED_LANGUAGES"):
                for lang in cls.SUPPORTED_LANGUAGES:
                    self._language_map[lang.lower()] = cls

            return cls

        return decorator

    def get(self, name: str) -> type[ChunkerPlugin]:
        """Get a registered chunker class by name.

        Args:
            name: Chunker type name

        Returns:
            The registered chunker class

        Raises:
            KeyError: If chunker is not registered
        """
        key = "chunkers"
        if key not in self._items or name not in self._items[key]:
            available = list(self._items.get(key, {}).keys())
            raise KeyError(f"Chunker '{name}' not registered. Available: {available}")
        return self._items[key][name]

    def get_for_language(self, language: str) -> type[ChunkerPlugin]:
        """Get the appropriate chunker class for a language.

        Falls back to the default chunker ("simple") if no specialized
        chunker is available for the language.

        Args:
            language: Language identifier (e.g., "python", "markdown")

        Returns:
            The most appropriate chunker class for the language
        """
        lang_lower = language.lower()
        if lang_lower in self._language_map:
            return self._language_map[lang_lower]
        # Default to simple chunker
        return self.get("simple")

    def list_chunkers(self) -> list[str]:
        """List all registered chunker names.

        Returns:
            List of registered chunker names
        """
        return list(self._items.get("chunkers", {}).keys())

    def is_registered(self, name: str) -> bool:
        """Check if a chunker is registered.

        Args:
            name: Chunker type name

        Returns:
            True if registered, False otherwise
        """
        return name in self._items.get("chunkers", {})

    def clear(self) -> None:
        """Clear all registrations (for testing purposes)."""
        if hasattr(self, "_items"):
            self._items.clear()
        if hasattr(self, "_language_map"):
            self._language_map.clear()

    # Backward compatibility: provide _chunkers as a property
    @property
    def _chunkers(self) -> dict[str, type[ChunkerPlugin]]:
        """Backward compatibility property for _chunkers."""
        return self._items.get("chunkers", {})

    @_chunkers.setter
    def _chunkers(self, value: dict[str, type[ChunkerPlugin]]) -> None:
        """Backward compatibility setter for _chunkers."""
        self._items["chunkers"] = value


# Global registry instance
registry = ChunkerRegistry()


# Auto-register built-in chunkers
def _register_builtin_chunkers() -> None:
    """Register built-in chunker implementations."""
    from .line import LineChunker
    from .markdown import MarkdownChunker
    from .simple import SimpleChunker

    # Register each built-in chunker directly
    for chunker_cls in [SimpleChunker, LineChunker, MarkdownChunker]:
        if chunker_cls.NAME not in registry._items.get("chunkers", {}):
            registry._items.setdefault("chunkers", {})[chunker_cls.NAME] = chunker_cls

            # Build language mapping
            for lang in chunker_cls.SUPPORTED_LANGUAGES:
                registry._language_map[lang.lower()] = chunker_cls


def _register_ast_chunkers() -> None:
    """Register AST chunker implementations (if tree-sitter is available)."""
    try:
        from .python_ast import PythonASTChunker

        if PythonASTChunker.NAME not in registry._items.get("chunkers", {}):
            registry._items.setdefault("chunkers", {})[PythonASTChunker.NAME] = PythonASTChunker
            for lang in PythonASTChunker.SUPPORTED_LANGUAGES:
                registry._language_map[lang.lower()] = PythonASTChunker
    except ImportError:
        pass  # tree-sitter not available

    try:
        from .typescript_ast import TypeScriptASTChunker

        if TypeScriptASTChunker.NAME not in registry._items.get("chunkers", {}):
            registry._items.setdefault("chunkers", {})[TypeScriptASTChunker.NAME] = (
                TypeScriptASTChunker
            )
            for lang in TypeScriptASTChunker.SUPPORTED_LANGUAGES:
                registry._language_map[lang.lower()] = TypeScriptASTChunker
    except ImportError:
        pass  # tree-sitter not available

    try:
        from .go_ast import GoASTChunker

        if GoASTChunker.NAME not in registry._items.get("chunkers", {}):
            registry._items.setdefault("chunkers", {})[GoASTChunker.NAME] = GoASTChunker
            for lang in GoASTChunker.SUPPORTED_LANGUAGES:
                registry._language_map[lang.lower()] = GoASTChunker
    except ImportError:
        pass  # tree-sitter not available


# Register built-ins on module import
_register_builtin_chunkers()
_register_ast_chunkers()
