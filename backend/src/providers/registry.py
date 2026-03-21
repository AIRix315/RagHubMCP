"""Provider registry for dynamic registration and lookup.

This module implements the registry pattern for provider management:
- ProviderRegistry: Singleton registry for provider classes
- Decorator-based registration
- Type-safe provider lookup
"""

from __future__ import annotations

from typing import Callable

from src.common.registry import Registry
from .base import ProviderCategory, BaseProvider, UnsupportedProviderError


class ProviderRegistry(Registry[BaseProvider, ProviderCategory]):
    """Provider registry with singleton pattern.
    
    Provides a central registration point for all provider types.
    Supports decorator-based registration and runtime lookup.
    
    Example:
        from providers.registry import registry
        from providers.base import ProviderCategory
        
        @registry.register(ProviderCategory.EMBEDDING, "ollama")
        class OllamaEmbeddingProvider(BaseEmbeddingProvider):
            ...
        
        # Later, retrieve the provider class
        provider_cls = registry.get(ProviderCategory.EMBEDDING, "ollama")
    """
    
    def __init__(self) -> None:
        """Initialize provider registry with default categories."""
        # Only initialize if not already done
        if not hasattr(self, '_initialized') or not self._initialized:
            self._items = {
                ProviderCategory.EMBEDDING: {},
                ProviderCategory.RERANK: {},
                ProviderCategory.LLM: {},
                ProviderCategory.VECTORSTORE: {},
            }
            self._initialized = True
    
    def register(
        self,
        category: ProviderCategory,
        name: str
    ) -> Callable[[type], type]:
        """Decorator to register a provider class.
        
        Args:
            category: Provider category (EMBEDDING, RERANK, LLM)
            name: Unique name for this provider type (e.g., "ollama", "openai")
            
        Returns:
            Decorator function that registers the class
            
        Raises:
            ValueError: If provider name is already registered in this category
            
        Example:
            @registry.register(ProviderCategory.EMBEDDING, "ollama")
            class OllamaEmbeddingProvider(BaseEmbeddingProvider):
                ...
        """
        def decorator(cls: type) -> type:
            if category not in self._items:
                self._items[category] = {}
            if name in self._items[category]:
                raise ValueError(
                    f"Provider '{name}' already registered in category '{category.value}'. "
                    f"Existing: {self._items[category][name]}"
                )
            self._items[category][name] = cls
            return cls
        return decorator
    
    def get(self, category: ProviderCategory, name: str) -> type[BaseProvider]:
        """Get a registered provider class by name.
        
        Args:
            category: Provider category
            name: Provider type name
            
        Returns:
            The registered provider class
            
        Raises:
            UnsupportedProviderError: If provider is not registered
        """
        if category not in self._items or name not in self._items[category]:
            available = list(self._items.get(category, {}).keys())
            raise UnsupportedProviderError(name, category.value, available)
        return self._items[category][name]
    
    def list_providers(self, category: ProviderCategory) -> list[str]:
        """List all registered provider names in a category.
        
        Args:
            category: Provider category
            
        Returns:
            List of registered provider names
        """
        return list(self._items.get(category, {}).keys())
    
    def is_registered(self, category: ProviderCategory, name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            category: Provider category
            name: Provider type name
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._items.get(category, {})
    
    def clear(self) -> None:
        """Clear all registrations (for testing purposes)."""
        self._items = {
            ProviderCategory.EMBEDDING: {},
            ProviderCategory.RERANK: {},
            ProviderCategory.LLM: {},
            ProviderCategory.VECTORSTORE: {},
        }


# Global registry instance
registry = ProviderRegistry()
