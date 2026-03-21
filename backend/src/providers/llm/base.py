"""LLM provider abstract base class.

This module defines the interface for Large Language Model providers
that generate text based on prompts.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

from ..base import BaseProvider


class BaseLLMProvider(BaseProvider):
    """Abstract base class for LLM providers.

    LLM providers generate text based on input prompts. They support
    both synchronous and asynchronous generation, with optional streaming.

    Subclasses must implement:
    - NAME: Class attribute for provider identification
    - generate(): Synchronous text generation
    - from_config(): Factory method to create instances from config

    Optional methods to override:
    - stream(): Streaming generation (default: yields complete response)
    - agenerate(): Async generation (default: wraps sync method)
    - astream(): Async streaming (default: wraps sync stream)

    Example:
        class MyLLMProvider(BaseLLMProvider):
            NAME = "my-llm"

            def generate(
                self,
                prompt: str,
                temperature: float = 0.7,
                max_tokens: int = 1024,
                **kwargs
            ) -> str:
                response = self._client.generate(prompt, temperature, max_tokens)
                return response.text

            @classmethod
            def from_config(cls, config: dict) -> "MyLLMProvider":
                return cls(
                    model=config["model"],
                    base_url=config.get("base_url")
                )
    """

    @abstractmethod
    def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs: Any
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Input text prompt
            temperature: Sampling temperature (0.0 to 1.0+).
                        Lower = more deterministic, higher = more random.
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text string

        Note:
            Implementations should handle API-specific parameters
            through **kwargs (e.g., top_p, frequency_penalty).
        """
        ...

    # =========================================================================
    # Async methods with default implementations
    # =========================================================================

    async def agenerate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs: Any
    ) -> str:
        """Async version of generate.

        Default implementation wraps the synchronous method using asyncio.to_thread.
        Subclasses can override for native async support.

        Args:
            prompt: Input text prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text string
        """
        return await asyncio.to_thread(self.generate, prompt, temperature, max_tokens, **kwargs)

    # =========================================================================
    # Streaming methods with default implementations
    # =========================================================================

    def stream(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs: Any
    ) -> Iterator[str]:
        """Stream generated text chunks.

        Default implementation yields the complete response as a single chunk.
        Override for true streaming support.

        Args:
            prompt: Input text prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Text chunks (strings)
        """
        yield self.generate(prompt, temperature, max_tokens, **kwargs)

    async def astream(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs: Any
    ) -> AsyncIterator[str]:
        """Async stream generated text chunks.

        Default implementation wraps the synchronous stream method.

        Args:
            prompt: Input text prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Text chunks (strings)
        """
        for chunk in self.stream(prompt, temperature, max_tokens, **kwargs):
            yield chunk
            await asyncio.sleep(0)  # Yield control to event loop

    # =========================================================================
    # Convenience methods for chat-style interactions
    # =========================================================================

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """Generate a response from a chat conversation.

        Default implementation formats messages into a single prompt.
        Override for native chat API support.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Role can be 'system', 'user', or 'assistant'.
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response string
        """
        # Default: concatenate messages into a single prompt
        formatted_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted_parts.append(f"[{role}]: {content}")

        prompt = "\n".join(formatted_parts)
        return self.generate(prompt, temperature, max_tokens, **kwargs)

    async def achat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """Async version of chat.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response string
        """
        return await asyncio.to_thread(self.chat, messages, temperature, max_tokens, **kwargs)

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> BaseLLMProvider:
        """Create an instance from configuration dictionary.

        Args:
            config: Configuration from config.yaml providers section.
                   Typically includes: name, type, model, base_url

        Returns:
            New provider instance
        """
        ...
