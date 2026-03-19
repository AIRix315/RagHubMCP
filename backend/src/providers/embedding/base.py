"""Embedding provider abstract base class.

This module defines the interface for embedding providers that convert
text into vector representations.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Any

from ..base import BaseProvider


class BaseEmbeddingProvider(BaseProvider):
    """Abstract base class for embedding providers.
    
    Embedding providers convert text into fixed-size vector representations
    that can be used for similarity search, clustering, and other ML tasks.
    
    Subclasses must implement:
    - NAME: Class attribute for provider identification
    - embed_documents(): Embed a list of documents
    - embed_query(): Embed a single query
    - dimension: Property returning the embedding dimension
    - from_config(): Factory method to create instances from config
    
    Async methods (aembed_documents, aembed_query) have default implementations
    that wrap the synchronous methods using asyncio.to_thread.
    
    Example:
        class MyEmbeddingProvider(BaseEmbeddingProvider):
            NAME = "my-embedding"
            
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [self._embed(text) for text in texts]
            
            def embed_query(self, query: str) -> list[float]:
                return self._embed(query)
            
            @property
            def dimension(self) -> int:
                return 768
            
            @classmethod
            def from_config(cls, config: dict) -> "MyEmbeddingProvider":
                return cls(model=config["model"])
    """
    
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors, one per document.
            Each vector is a list of floats with length equal to self.dimension.
            
        Note:
            Some embedding models differentiate between documents and queries.
            Use embed_query() for query texts.
        """
        ...
    
    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector as a list of floats
            
        Note:
            Some models (e.g., E5, BGE) use different prefixes for queries
            vs documents. This method handles query-specific processing.
        """
        ...
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension.
        
        Returns:
            Number of dimensions in the embedding vectors
        """
        ...
    
    # =========================================================================
    # Async methods with default implementations
    # =========================================================================
    
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async version of embed_documents.
        
        Default implementation wraps the synchronous method using asyncio.to_thread.
        Subclasses can override for native async support.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        return await asyncio.to_thread(self.embed_documents, texts)
    
    async def aembed_query(self, query: str) -> list[float]:
        """Async version of embed_query.
        
        Default implementation wraps the synchronous method using asyncio.to_thread.
        Subclasses can override for native async support.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        return await asyncio.to_thread(self.embed_query, query)
    
    # =========================================================================
    # Optional methods for batch processing
    # =========================================================================
    
    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> list[list[float]]:
        """Embed texts in batches.
        
        Default implementation processes all texts at once.
        Override for memory-efficient batch processing.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per batch (for API limits)
            
        Returns:
            List of embedding vectors
        """
        return self.embed_documents(texts)
    
    async def aembed_batch(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> list[list[float]]:
        """Async batch embedding.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per batch
            
        Returns:
            List of embedding vectors
        """
        return await asyncio.to_thread(self.embed_batch, texts, batch_size)
    
    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> BaseEmbeddingProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Typically includes: name, type, model, base_url, dimension
            
        Returns:
            New provider instance
            
        Raises:
            ProviderInitializationError: If configuration is invalid
        """
        ...