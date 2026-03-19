"""Chunker registry for dynamic registration and lookup.

This module implements the registry pattern for chunker management:
- ChunkerRegistry: Singleton registry for chunker classes
- Decorator-based registration
- Language-aware chunker selection
"""

from __future__ import annotations

from typing import Callable

from .base import ChunkerPlugin


class ChunkerRegistry:
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
    
    _instance: ChunkerRegistry | None = None
    _chunkers: dict[str, type[ChunkerPlugin]] = {}
    _language_map: dict[str, type[ChunkerPlugin]] = {}
    
    def __new__(cls) -> ChunkerRegistry:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._chunkers = {}
            cls._instance._language_map = {}
        return cls._instance
    
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
            if name in self._chunkers:
                raise ValueError(
                    f"Chunker '{name}' already registered. Existing: "
                    f"{self._chunkers[name]}"
                )
            self._chunkers[name] = cls
            
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
        if name not in self._chunkers:
            available = list(self._chunkers.keys())
            raise KeyError(
                f"Chunker '{name}' not registered. Available: {available}"
            )
        return self._chunkers[name]
    
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
        return list(self._chunkers.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if a chunker is registered.
        
        Args:
            name: Chunker type name
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._chunkers
    
    def clear(self) -> None:
        """Clear all registrations (for testing purposes)."""
        self._chunkers.clear()
        self._language_map.clear()


# Global registry instance
registry = ChunkerRegistry()


# Auto-register built-in chunkers
def _register_builtin_chunkers() -> None:
    """Register built-in chunker implementations."""
    from .simple import SimpleChunker
    from .line import LineChunker
    from .markdown import MarkdownChunker
    
    # Register each built-in chunker
    for chunker_cls in [SimpleChunker, LineChunker, MarkdownChunker]:
        if chunker_cls.NAME not in registry._chunkers:
            registry._chunkers[chunker_cls.NAME] = chunker_cls
            
            # Build language mapping
            for lang in chunker_cls.SUPPORTED_LANGUAGES:
                registry._language_map[lang.lower()] = chunker_cls


# Register built-ins on module import
_register_builtin_chunkers()