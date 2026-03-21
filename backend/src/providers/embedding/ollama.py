"""Ollama embedding provider implementation.

This module provides an embedding provider that uses Ollama's local API
for generating text embeddings using various models like nomic-embed-text,
bge-m3, etc.

Reference: https://ollama.com/blog/embedding-models
"""

from __future__ import annotations

from typing import Any

import httpx

from ..base import ProviderCategory
from ..registry import registry
from .base import BaseEmbeddingProvider
from src.utils.config import ProviderDefaultsConfig


# Default Ollama API endpoint
DEFAULT_BASE_URL = "http://localhost:11434"


@registry.register(ProviderCategory.EMBEDDING, "ollama")
class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Ollama-based embedding provider.
    
    Uses Ollama's /api/embeddings endpoint to generate text embeddings.
    Supports any embedding model available in Ollama (nomic-embed-text,
    bge-m3, mxbai-embed-large, etc.).
    
    Attributes:
        NAME: Provider type identifier ("ollama")
        model: Ollama model name
        base_url: Ollama API endpoint URL
        dimension: Embedding dimension
    
    Example:
        >>> provider = OllamaEmbeddingProvider(
        ...     model="nomic-embed-text",
        ...     base_url="http://localhost:11434"
        ... )
        >>> embedding = provider.embed_query("Hello world")
        >>> len(embedding)
        768
    """
    
    NAME = "ollama"
    
    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = DEFAULT_BASE_URL,
        dimension: int = ProviderDefaultsConfig().default_embedding_dimension,
    ) -> None:
        """Initialize Ollama embedding provider.
        
        Args:
            model: Ollama model name. Options include:
                - "nomic-embed-text" (768 dims, good general purpose)
                - "bge-m3" (1024 dims, multilingual)
                - "mxbai-embed-large" (1024 dims, high quality)
            base_url: Ollama API endpoint URL.
                      Default: "http://localhost:11434"
            dimension: Embedding dimension. Should match model output.
                       Default: 768 (from ProviderDefaultsConfig)
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dimension = dimension
    
    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model
    
    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._base_url
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension
    
    def _get_embedding_url(self) -> str:
        """Get the full embedding API URL."""
        return f"{self._base_url}/api/embeddings"
    
    def _embed_single(self, text: str) -> list[float]:
        """Embed a single text using Ollama API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = httpx.post(
            self._get_embedding_url(),
            json={"model": self._model, "prompt": text},
            timeout=ProviderDefaultsConfig().embedding_timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]
    
    def _embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single request.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = httpx.post(
            self._get_embedding_url(),
            json={"model": self._model, "prompt": texts},
            timeout=ProviderDefaultsConfig().embedding_timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"]
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Use batch endpoint if available, otherwise fall back to individual
        try:
            return self._embed_batch_sync(texts)
        except Exception:
            # Fall back to individual embeddings
            return [self._embed_single(text) for text in texts]
    
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        return self._embed_single(query)
    
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async embed a list of documents.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_embedding_url(),
                json={"model": self._model, "prompt": texts},
                timeout=ProviderDefaultsConfig().embedding_timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]
    
    async def aembed_query(self, query: str) -> list[float]:
        """Async embed a single query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_embedding_url(),
                json={"model": self._model, "prompt": query},
                timeout=ProviderDefaultsConfig().embedding_timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
    
    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> list[list[float]]:
        """Embed texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        results: list[list[float]] = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._embed_batch_sync(batch)
            results.extend(batch_embeddings)
        
        return results
    
    @classmethod
    def from_config(cls, config: dict[str, Any]) -> OllamaEmbeddingProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - model: Ollama model name (required)
                   - base_url: Ollama API URL (optional)
                   - dimension: Embedding dimension (optional)
            
        Returns:
            New OllamaEmbeddingProvider instance
        """
        return cls(
            model=config.get("model", "nomic-embed-text"),
            base_url=config.get("base_url", DEFAULT_BASE_URL),
            dimension=config.get("dimension", ProviderDefaultsConfig().default_embedding_dimension),
        )