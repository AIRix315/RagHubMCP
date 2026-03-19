"""Provider factory with singleton caching.

This module implements the factory pattern for provider instantiation:
- ProviderFactory: Creates provider instances from configuration
- Singleton caching: Reuses instances with same configuration
- Configuration-driven: Integrates with config.yaml
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.utils.config import get_config

from .base import (
    ProviderCategory,
    BaseProvider,
    ProviderInitializationError,
    ProviderNotFoundError,
)
from .registry import registry


class ProviderFactory:
    """Provider factory with singleton caching.
    
    Creates provider instances based on YAML configuration and caches
    them for reuse. The cache key is based on the full configuration,
    so different configurations get different instances.
    
    Example:
        from providers.factory import factory
        
        # Get the default embedding provider
        embedding = factory.get_embedding_provider()
        
        # Get a specific provider by name
        reranker = factory.get_rerank_provider("flashrank-mini")
    """
    
    _instance: ProviderFactory | None = None
    _cache: dict[str, BaseProvider]
    
    def __new__(cls) -> ProviderFactory:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance
    
    def _cache_key(
        self,
        category: ProviderCategory,
        name: str,
        config: dict[str, Any]
    ) -> str:
        """Generate a unique cache key for a provider configuration.
        
        The key is based on the category, name, and full configuration hash.
        This ensures that different configurations get different cache entries.
        
        Args:
            category: Provider category
            name: Provider instance name
            config: Full configuration dictionary
            
        Returns:
            Unique cache key string
        """
        config_str = json.dumps(config, sort_keys=True, default=str)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
        return f"{category.value}:{name}:{config_hash}"
    
    def get_embedding_provider(self, name: str | None = None) -> BaseEmbeddingProvider:
        """Get an embedding provider instance.
        
        Args:
            name: Provider instance name from config.yaml.
                  If None, uses the default provider.
                  
        Returns:
            BaseEmbeddingProvider instance
            
        Raises:
            ProviderNotFoundError: If provider instance not found in config
            ProviderInitializationError: If provider fails to initialize
        """
        return self._get_provider(ProviderCategory.EMBEDDING, name)
    
    def get_rerank_provider(self, name: str | None = None) -> BaseRerankProvider:
        """Get a rerank provider instance.
        
        Args:
            name: Provider instance name from config.yaml.
                  If None, uses the default provider.
                  
        Returns:
            BaseRerankProvider instance
        """
        return self._get_provider(ProviderCategory.RERANK, name)
    
    def get_llm_provider(self, name: str | None = None) -> BaseLLMProvider:
        """Get an LLM provider instance.
        
        Args:
            name: Provider instance name from config.yaml.
                  If None, uses the default provider.
                  
        Returns:
            BaseLLMProvider instance
        """
        return self._get_provider(ProviderCategory.LLM, name)
    
    def get_vectorstore_provider(self, name: str | None = None) -> BaseVectorStoreProvider:
        """Get a vector store provider instance.
        
        Args:
            name: Provider instance name from config.yaml.
                  If None, uses the default provider.
                  
        Returns:
            BaseVectorStoreProvider instance
        """
        return self._get_provider(ProviderCategory.VECTORSTORE, name)
    
    def _get_provider(
        self,
        category: ProviderCategory,
        name: str | None = None
    ) -> BaseProvider:
        """Internal method to get a provider instance.
        
        Flow:
        1. Load configuration
        2. Resolve provider name (default if not specified)
        3. Find instance configuration
        4. Check cache
        5. Create and cache if not found
        
        Args:
            category: Provider category
            name: Optional provider instance name
            
        Returns:
            Provider instance
        """
        config = get_config()
        category_config = getattr(config.providers, category.value, None)
        
        if category_config is None:
            raise ProviderInitializationError(
                provider="unknown",
                reason=f"No configuration found for category '{category.value}'"
            )
        
        # Resolve provider name
        provider_name = name or category_config.default
        if not provider_name:
            raise ProviderInitializationError(
                provider="unknown",
                reason=f"No default provider configured for {category.value}"
            )
        
        # Find instance configuration
        instance_config = None
        for inst in category_config.instances:
            if inst.get("name") == provider_name:
                instance_config = inst
                break
        
        if instance_config is None:
            available = [i.get("name") for i in category_config.instances]
            raise ProviderNotFoundError(provider_name, category.value, available)
        
        # Check cache
        cache_key = self._cache_key(category, provider_name, instance_config)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get provider class from registry
        provider_type = instance_config.get("type")
        provider_class = registry.get(category, provider_type)
        
        # Create instance
        try:
            instance = provider_class.from_config(instance_config)
            self._cache[cache_key] = instance
            return instance
        except Exception as e:
            raise ProviderInitializationError(
                provider=provider_name,
                reason=str(e)
            ) from e
    
    def clear_cache(self) -> None:
        """Clear the instance cache.
        
        Call this after configuration hot-reload to ensure
        new instances are created with updated configuration.
        """
        self._cache.clear()


# Type hints for forward references
from .embedding.base import BaseEmbeddingProvider
from .rerank.base import BaseRerankProvider
from .llm.base import BaseLLMProvider
from .vectorstore.base import BaseVectorStoreProvider


# Global factory instance
factory = ProviderFactory()