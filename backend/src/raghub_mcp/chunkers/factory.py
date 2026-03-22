"""Chunker Factory for configuration-driven instantiation.

This module provides a factory pattern for creating chunker instances,
similar to the ProviderFactory pattern used for providers.

Reference: RULE-3 - No direct dependency on concrete implementations.
"""

from __future__ import annotations

import logging
from typing import Any

from raghub_mcp.utils.config import get_config

from .base import ChunkerPlugin
from .registry import ChunkerRegistry, registry

logger = logging.getLogger(__name__)


class ChunkerFactory:
    """Factory for creating chunker instances.

    Similar to ProviderFactory, this factory creates chunker instances
    based on configuration, supporting hot reloading and caching.

    The factory provides:
    - Name-based chunker lookup
    - File type-based automatic selection
    - Instance caching for performance
    - Configuration-driven instantiation

    Reference: RULE-3 - No direct dependency on concrete implementations.

    Example:
        from chunkers import factory

        # Get chunker by name
        chunker = factory.get_chunker(name="markdown", chunk_size=500)

        # Get chunker for a file type
        chunker = factory.get_chunker(file_type=".py")

        # Get default chunker
        chunker = factory.get_chunker()
    """

    def __init__(self) -> None:
        """Initialize chunker factory."""
        self._registry = registry
        self._cache: dict[str, ChunkerPlugin] = {}
        self._config = get_config()

    def get_chunker(
        self,
        name: str | None = None,
        file_type: str | None = None,
        **config: Any,
    ) -> ChunkerPlugin:
        """Get a chunker instance.

        Args:
            name: Chunker name (e.g., "simple", "markdown", "python_ast")
            file_type: File extension to determine chunker (e.g., ".py", ".md")
            **config: Chunker configuration (chunk_size, overlap, etc.)

        Returns:
            Configured ChunkerPlugin instance

        Raises:
            KeyError: If named chunker is not registered
            ValueError: If neither name nor file_type is provided and no default exists

        Example:
            >>> chunker = factory.get_chunker(name="markdown", chunk_size=1000)
            >>> chunks = chunker.chunk("# Title\\n\\nContent...")
        """
        if name:
            return self._get_by_name(name, **config)
        elif file_type:
            return self._get_by_file_type(file_type, **config)
        else:
            # Default chunker from configuration or "simple"
            default_name = self._config.indexer.chunk_size if hasattr(self._config, 'indexer') else "simple"
            if isinstance(default_name, int):
                default_name = "simple"
            return self._get_by_name(default_name, **config)

    def _get_by_name(self, name: str, **config: Any) -> ChunkerPlugin:
        """Get chunker by name with caching.

        Args:
            name: Chunker name
            **config: Chunker configuration

        Returns:
            ChunkerPlugin instance

        Raises:
            KeyError: If chunker is not registered
        """
        # Generate cache key from name and config
        config_key = ",".join(f"{k}={v}" for k, v in sorted(config.items()))
        cache_key = f"{name}:{config_key}"

        if cache_key not in self._cache:
            chunker_class = self._registry.get(name)
            self._cache[cache_key] = chunker_class(**config)
            logger.debug(f"Created chunker instance: {name}")

        return self._cache[cache_key]

    def _get_by_file_type(self, file_type: str, **config: Any) -> ChunkerPlugin:
        """Get chunker by file type.

        Maps file extensions to appropriate chunkers:
        - .md, .markdown -> markdown
        - .py -> python_ast
        - .ts, .tsx, .js, .jsx -> typescript_ast
        - .go -> go_ast
        - others -> simple

        Args:
            file_type: File extension (e.g., ".py", ".md")
            **config: Chunker configuration

        Returns:
            ChunkerPlugin instance
        """
        # Normalize file type
        ext = file_type.lower()
        if not ext.startswith("."):
            ext = "." + ext

        # Map file types to chunker names
        type_map: dict[str, str] = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".py": "python_ast",
            ".ts": "typescript_ast",
            ".tsx": "typescript_ast",
            ".js": "typescript_ast",
            ".jsx": "typescript_ast",
            ".go": "go_ast",
        }

        name = type_map.get(ext, "simple")

        # Try to get AST chunker, fall back to simple if not available
        try:
            return self._get_by_name(name, **config)
        except KeyError:
            logger.debug(f"AST chunker '{name}' not available, using 'simple'")
            return self._get_by_name("simple", **config)

    def clear_cache(self) -> None:
        """Clear cached chunker instances.

        Call this after configuration changes to ensure
        new instances are created with updated settings.
        """
        self._cache.clear()
        logger.debug("Chunker cache cleared")

    def list_available(self) -> list[str]:
        """List all available chunker names.

        Returns:
            List of registered chunker names
        """
        return self._registry.list_chunkers()

    def is_available(self, name: str) -> bool:
        """Check if a chunker is available.

        Args:
            name: Chunker name to check

        Returns:
            True if chunker is registered and available
        """
        return self._registry.is_registered(name)


# Singleton instance (module-level)
factory = ChunkerFactory()


def get_chunker_factory() -> ChunkerFactory:
    """Get the global ChunkerFactory instance.

    Returns:
        The singleton ChunkerFactory instance
    """
    return factory


def reset_chunker_factory() -> None:
    """Reset the global ChunkerFactory instance.

    Clears the cache and creates a new factory instance.
    Useful for testing or when configuration changes.
    """
    global factory
    factory = ChunkerFactory()
    logger.debug("ChunkerFactory reset")
