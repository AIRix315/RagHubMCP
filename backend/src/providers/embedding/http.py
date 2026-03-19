"""HTTP embedding provider implementation.

This module provides a generic HTTP embedding provider that supports all
OpenAI-compatible APIs including:
- OpenAI official API
- Azure OpenAI
- LM Studio
- LocalAI
- vLLM
- Any other OpenAI-compatible service

Reference: https://platform.openai.com/docs/api-reference/embeddings
"""

from __future__ import annotations

from typing import Any

import httpx

from ..base import ProviderCategory
from ..registry import registry
from .base import BaseEmbeddingProvider


@registry.register(ProviderCategory.EMBEDDING, "http")
class HTTPEmbeddingProvider(BaseEmbeddingProvider):
    """Generic HTTP embedding provider for OpenAI-compatible APIs.
    
    This provider supports any embedding service that implements the
    OpenAI embeddings API format:
    
    - POST {base_url}/embeddings
    - Request body: {"input": [...], "model": "..."}
    - Response: {"data": [{"embedding": [...], "index": 0}, ...]}
    
    Supports:
    - OpenAI official API (text-embedding-3-small, text-embedding-3-large, etc.)
    - Azure OpenAI
    - LM Studio
    - LocalAI
    - vLLM
    - Any OpenAI-compatible service
    
    Attributes:
        NAME: Provider type identifier ("http")
        model: Model identifier
        base_url: API endpoint URL
        dimension: Embedding dimension
        api_key: Optional API key for authentication
        headers: Optional custom headers
    
    Example:
        >>> # OpenAI via HTTP
        >>> provider = HTTPEmbeddingProvider(
        ...     base_url="https://api.openai.com/v1",
        ...     model="text-embedding-3-small",
        ...     dimension=1536,
        ...     api_key="sk-xxx"
        ... )
        
        >>> # LM Studio
        >>> provider = HTTPEmbeddingProvider(
        ...     base_url="http://localhost:1234/v1",
        ...     model="nomic-embed-text",
        ...     dimension=768
        ... )
        
        >>> # Azure OpenAI
        >>> provider = HTTPEmbeddingProvider(
        ...     base_url="https://your-resource.openai.azure.com/openai/deployments/your-deployment",
        ...     model="text-embedding-ada-002",
        ...     dimension=1536,
        ...     api_key="azure-key",
        ...     headers={"api-key": "azure-key"}
        ... )
    """
    
    NAME = "http"
    
    def __init__(
        self,
        base_url: str,
        model: str,
        dimension: int,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize HTTP embedding provider.
        
        Args:
            base_url: Base URL for the embedding API.
                      Examples:
                      - "https://api.openai.com/v1"
                      - "http://localhost:1234/v1"
                      - "https://your-resource.openai.azure.com/openai/deployments/your-deployment"
            model: Model identifier.
                   Examples: "text-embedding-3-small", "nomic-embed-text"
            dimension: Embedding dimension. Should match model output.
            api_key: Optional API key. Will be sent as Bearer token in
                     Authorization header.
            headers: Optional custom headers. Useful for Azure OpenAI which
                     requires "api-key" header.
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dimension = dimension
        self._api_key = api_key
        self._custom_headers = headers or {}
    
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
    
    def _get_embeddings_url(self) -> str:
        """Get the full embeddings API URL."""
        return f"{self._base_url}/embeddings"
    
    def _get_headers(self) -> dict[str, str]:
        """Build request headers.
        
        Returns:
            Headers dict with Content-Type and optional Authorization.
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add custom headers first (e.g., Azure's "api-key")
        headers.update(self._custom_headers)
        
        # Add Bearer token if API key provided (for OpenAI-compatible APIs)
        if self._api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._api_key}"
        
        return headers
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        response = httpx.post(
            self._get_embeddings_url(),
            json={
                "input": texts,
                "model": self._model,
            },
            headers=self._get_headers(),
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        
        # Sort by index to ensure correct order
        embeddings_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]
    
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        response = httpx.post(
            self._get_embeddings_url(),
            json={
                "input": query,
                "model": self._model,
            },
            headers=self._get_headers(),
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    
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
                self._get_embeddings_url(),
                json={
                    "input": texts,
                    "model": self._model,
                },
                headers=self._get_headers(),
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            
            embeddings_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings_data]
    
    async def aembed_query(self, query: str) -> list[float]:
        """Async embed a single query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_embeddings_url(),
                json={
                    "input": query,
                    "model": self._model,
                },
                headers=self._get_headers(),
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    
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
            batch_embeddings = self.embed_documents(batch)
            results.extend(batch_embeddings)
        
        return results
    
    @classmethod
    def from_config(cls, config: dict[str, Any]) -> HTTPEmbeddingProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - base_url: API endpoint URL (required)
                   - model: Model identifier (required)
                   - dimension: Embedding dimension (required)
                   - api_key: API key for authentication (optional)
                   - headers: Custom headers (optional)
        
        Returns:
            New HTTPEmbeddingProvider instance
        """
        return cls(
            base_url=config["base_url"],
            model=config["model"],
            dimension=config["dimension"],
            api_key=config.get("api_key"),
            headers=config.get("headers"),
        )