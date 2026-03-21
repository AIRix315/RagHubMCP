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
    BaseProvider,
    ProviderCategory,
    ProviderError,
    ProviderInitializationError,
    ProviderNotFoundError,
    UnsupportedProviderError,
)
from .factory import ProviderFactory, factory
from .registry import ProviderRegistry, registry

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
