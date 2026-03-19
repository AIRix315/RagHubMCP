"""Providers module for RagHubMCP.

This module provides the provider abstraction layer including:
- Base classes for Embedding, Rerank, and LLM providers
- Provider registry for dynamic registration
- Provider factory for configuration-driven instantiation

Example:
    from providers import BaseEmbeddingProvider, registry, factory
    
    # Register a custom provider
    @registry.register(ProviderCategory.EMBEDDING, "custom")
    class CustomEmbedding(BaseEmbeddingProvider):
        ...
    
    # Get a provider instance from config
    embedding = factory.get_embedding_provider()
"""

from .base import (
    ProviderCategory,
    ProviderError,
    UnsupportedProviderError,
    ProviderInitializationError,
    ProviderNotFoundError,
    BaseProvider,
)
from .registry import registry, ProviderRegistry
from .factory import factory, ProviderFactory

__all__ = [
    # Enums
    "ProviderCategory",
    # Exceptions
    "ProviderError",
    "UnsupportedProviderError",
    "ProviderInitializationError",
    "ProviderNotFoundError",
    # Base classes
    "BaseProvider",
    # Registry
    "registry",
    "ProviderRegistry",
    # Factory
    "factory",
    "ProviderFactory",
]