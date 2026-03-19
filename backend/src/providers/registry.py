"""Provider registry for dynamic registration and lookup.

This module implements the registry pattern for provider management:
- ProviderRegistry: Singleton registry for provider classes
- Decorator-based registration
- Type-safe provider lookup
"""

from __future__ import annotations

from typing import Callable

from .base import ProviderCategory, BaseProvider, UnsupportedProviderError


class ProviderRegistry:
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
    
    _instance: ProviderRegistry | None = None
    _providers: dict[ProviderCategory, dict[str, type[BaseProvider]]]
    
    def __new__(cls) -> ProviderRegistry:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {
                ProviderCategory.EMBEDDING: {},
                ProviderCategory.RERANK: {},
                ProviderCategory.LLM: {},
            }
        return cls._instance
    
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
            if name in self._providers[category]:
                raise ValueError(
                    f"Provider '{name}' already registered in category '{category.value}'. "
                    f"Existing: {self._providers[category][name]}"
                )
            self._providers[category][name] = cls
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
        if name not in self._providers[category]:
            available = list(self._providers[category].keys())
            raise UnsupportedProviderError(name, category.value, available)
        return self._providers[category][name]
    
    def list_providers(self, category: ProviderCategory) -> list[str]:
        """List all registered provider names in a category.
        
        Args:
            category: Provider category
            
        Returns:
            List of registered provider names
        """
        return list(self._providers[category].keys())
    
    def is_registered(self, category: ProviderCategory, name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            category: Provider category
            name: Provider type name
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._providers[category]
    
    def clear(self) -> None:
        """Clear all registrations (for testing purposes)."""
        for category in self._providers:
            self._providers[category] = {}


# Global registry instance
registry = ProviderRegistry()