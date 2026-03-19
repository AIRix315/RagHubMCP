"""Provider abstraction layer base classes and exceptions.

This module defines the foundational components for the provider system:
- ProviderCategory: Enum for provider categories (embedding, rerank, llm)
- ProviderError: Base exception class with structured error information
- BaseProvider: Abstract base class for all providers
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderCategory(str, Enum):
    """Provider category enumeration.
    
    Defines the three main categories of providers in RagHubMCP:
    - EMBEDDING: Vector embedding providers (Ollama, OpenAI, etc.)
    - RERANK: Document reranking providers (FlashRank, etc.)
    - LLM: Large language model providers (Ollama, OpenAI, etc.)
    """
    EMBEDDING = "embedding"
    RERANK = "rerank"
    LLM = "llm"


# =============================================================================
# Exception Classes
# =============================================================================

@dataclass
class ProviderError(Exception):
    """Base exception class for provider-related errors.
    
    Provides structured error information including:
    - message: Human-readable error description
    - provider: Name of the provider that caused the error
    - error_code: Machine-readable error code
    - details: Additional context as a dictionary
    
    Example:
        >>> error = ProviderError(
        ...     message="Connection failed",
        ...     provider="openai",
        ...     error_code="CONNECTION_ERROR"
        ... )
        >>> str(error)
        '[openai] CONNECTION_ERROR: Connection failed'
    """
    message: str
    provider: str
    error_code: str = "UNKNOWN"
    details: dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"[{self.provider}] {self.error_code}: {self.message}"


class UnsupportedProviderError(ProviderError):
    """Raised when a requested provider type is not supported.
    
    This error indicates that the provider type is not registered
    in the provider registry. The error message includes the list
    of available providers for the requested category.
    
    Example:
        >>> raise UnsupportedProviderError("unknown", "embedding", ["ollama", "openai"])
    """
    
    def __init__(self, provider: str, category: str, available: list[str]):
        super().__init__(
            message=f"Provider '{provider}' not supported in category '{category}'. "
                    f"Available: {available}",
            provider=provider,
            error_code="UNSUPPORTED_PROVIDER",
            details={"category": category, "available": available}
        )


class ProviderInitializationError(ProviderError):
    """Raised when a provider fails to initialize.
    
    This error wraps underlying exceptions during provider
    instantiation and provides additional context.
    
    Example:
        >>> raise ProviderInitializationError("openai", "Invalid API key")
    """
    
    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"Failed to initialize: {reason}",
            provider=provider,
            error_code="INITIALIZATION_FAILED",
            details={"reason": reason}
        )


class ProviderNotFoundError(ProviderError):
    """Raised when a provider instance is not found in configuration.
    
    This error indicates that the requested provider instance name
    does not exist in the configuration file.
    
    Example:
        >>> raise ProviderNotFoundError("my-embedding", "embedding", ["default", "ollama-local"])
    """
    
    def __init__(self, provider: str, category: str, available: list[str]):
        super().__init__(
            message=f"Provider instance '{provider}' not found in configuration for '{category}'. "
                    f"Available: {available}",
            provider=provider,
            error_code="PROVIDER_NOT_FOUND",
            details={"category": category, "available": available}
        )


# =============================================================================
# Base Provider Class
# =============================================================================

class BaseProvider(ABC):
    """Abstract base class for all providers.
    
    This class defines the common interface that all providers must implement.
    It uses the Template Method pattern to ensure consistent behavior across
    different provider types.
    
    Subclasses must implement:
    - NAME: Class attribute identifying the provider type
    - from_config(): Class method to create instances from configuration
    
    Class Attributes:
        NAME: Unique identifier for this provider type (e.g., "ollama", "openai")
    
    Example:
        class MyEmbeddingProvider(BaseEmbeddingProvider):
            NAME = "my-provider"
            
            @classmethod
            def from_config(cls, config: dict) -> "MyEmbeddingProvider":
                return cls(model=config["model"])
    """
    
    # Class attribute: Provider type name (must be overridden by concrete subclasses)
    NAME: str
    
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that concrete subclasses define required class attributes.
        
        Only enforces NAME for non-abstract classes (those that can be instantiated).
        Abstract intermediate classes like BaseEmbeddingProvider don't need NAME.
        """
        super().__init_subclass__(**kwargs)
        # Only check NAME for concrete (non-abstract) classes
        # inspect.isabstract returns True if the class has unimplemented abstract methods
        if not inspect.isabstract(cls):
            if not hasattr(cls, 'NAME') or not isinstance(cls.NAME, str) or not cls.NAME:
                raise TypeError(
                    f"Concrete provider class {cls.__name__} must define a non-empty 'NAME' class attribute"
                )
    
    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> BaseProvider:
        """Create a provider instance from a configuration dictionary.
        
        This factory method is used by ProviderFactory to instantiate
        providers based on YAML configuration.
        
        Args:
            config: Configuration dictionary from config.yaml, typically
                   containing keys like 'name', 'type', 'model', 'base_url'
        
        Returns:
            A new provider instance
        
        Raises:
            ProviderInitializationError: If configuration is invalid
        
        Example:
            >>> config = {"type": "ollama", "model": "nomic-embed-text", "base_url": "http://localhost:11434"}
            >>> provider = OllamaEmbeddingProvider.from_config(config)
        """
        ...