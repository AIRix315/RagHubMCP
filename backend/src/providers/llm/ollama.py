"""Ollama LLM provider implementation.

This module provides an LLM provider that uses Ollama's local API
for generating text using various models like qwen2.5, llama3, etc.

Reference: https://ollama.com/blog/
"""

from __future__ import annotations

from typing import Any

import httpx

from ..base import ProviderCategory
from ..registry import registry
from .base import BaseLLMProvider

# Default Ollama API endpoint
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_TIMEOUT = 120.0  # LLM needs longer timeout


@registry.register(ProviderCategory.LLM, "ollama")
class OllamaLLMProvider(BaseLLMProvider):
    """Ollama-based LLM provider.

    Uses Ollama's /api/generate endpoint to generate text.
    Supports any LLM model available in Ollama (qwen2.5, llama3, mistral, etc.).

    Attributes:
        NAME: Provider type identifier ("ollama")
        model: Ollama model name
        base_url: Ollama API endpoint URL
        timeout: Request timeout in seconds

    Example:
        >>> provider = OllamaLLMProvider(
        ...     model="qwen2.5:7b",
        ...     base_url="http://localhost:11434"
        ... )
        >>> response = provider.generate("Hello, who are you?")
        >>> print(response)
        I am an AI assistant...
    """

    NAME = "ollama"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize Ollama LLM provider.

        Args:
            model: Ollama model name. Options include:
                - "qwen2.5:7b" (balanced performance/quality)
                - "llama3:8b" (Meta's Llama 3)
                - "mistral:7b" (Mistral AI's model)
            base_url: Ollama API endpoint URL.
                      Default: "http://localhost:11434"
            timeout: Request timeout in seconds.
                     Default: 120.0 (LLM generation can be slow)
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._base_url

    @property
    def timeout(self) -> float:
        """Get the timeout."""
        return self._timeout

    def _get_generate_url(self) -> str:
        """Get the full generate API URL."""
        return f"{self._base_url}/api/generate"

    def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs: Any
    ) -> str:
        """Generate text from a prompt using Ollama API.

        Args:
            prompt: Input text prompt
            temperature: Sampling temperature (0.0 to 1.0+).
                        Lower = more deterministic, higher = more random.
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text string

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        response = httpx.post(
            self._get_generate_url(),
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> OllamaLLMProvider:
        """Create an instance from configuration dictionary.

        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - model: Ollama model name (optional, default: qwen2.5:7b)
                   - base_url: Ollama API URL (optional)
                   - timeout: Request timeout in seconds (optional)

        Returns:
            New OllamaLLMProvider instance
        """
        return cls(
            model=config.get("model", DEFAULT_MODEL),
            base_url=config.get("base_url", DEFAULT_BASE_URL),
            timeout=config.get("timeout", DEFAULT_TIMEOUT),
        )
