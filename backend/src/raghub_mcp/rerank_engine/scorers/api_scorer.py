"""API-based rerank scorer for external rerank services.

This module implements scorers for external rerank APIs like Cohere and Jina,
with retry logic and rate limiting.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
Reference: Docs/22-Config-API-Design.md Section 2.2
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import abstractmethod
from typing import Any

import numpy as np

from ..core.scorer import BaseScorer

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: int = 100):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute.
        """
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire rate limit permission, waiting if necessary."""
        async with self._lock:
            now = time.time()
            time_since_last = now - self._last_request_time
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            self._last_request_time = time.time()


class APIScorerError(Exception):
    """Exception raised when API scorer fails."""

    def __init__(self, message: str, provider: str, status_code: int | None = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class APIScorer(BaseScorer):
    """Base class for API-based rerank scorers.

    Provides common functionality for external rerank APIs:
    - Retry logic with exponential backoff
    - Rate limiting
    - Error handling
    """

    def __init__(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_per_minute: int = 100,
    ):
        """Initialize API scorer.

        Args:
            provider: Provider name (cohere, jina).
            api_key: API key for authentication.
            base_url: API base URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            rate_limit_per_minute: Rate limit for API calls.
        """
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._rate_limiter = RateLimiter(rate_limit_per_minute)

    @property
    def name(self) -> str:
        return f"api-{self._provider}"

    @property
    def supports_batch(self) -> bool:
        return True

    @property
    @abstractmethod
    def provider(self) -> str:
        """Provider name."""
        ...

    @abstractmethod
    def _build_request_body(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> dict[str, Any]:
        """Build request body for the API.

        Args:
            query: Query string.
            documents: Document list.
            top_n: Number of results to return.

        Returns:
            Request body dictionary.
        """
        ...

    @abstractmethod
    def _parse_response(self, response: dict[str, Any]) -> list[float]:
        """Parse API response to extract scores.

        Args:
            response: API response dictionary.

        Returns:
            List of scores in document order.
        """
        ...

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Get request headers.

        Returns:
            Headers dictionary.
        """
        ...

    async def _make_request(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[float]:
        """Make API request with retry logic.

        Args:
            query: Query string.
            documents: Document list.
            top_n: Number of results to return.

        Returns:
            List of scores.

        Raises:
            APIScorerError: If all retries fail.
        """
        import httpx

        url = f"{self._base_url}/rerank"
        headers = self._get_headers()
        body = self._build_request_body(query, documents, top_n)

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                # Rate limiting
                await self._rate_limiter.acquire()

                # Make request
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=body, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_response(data)

                    elif response.status_code == 429:
                        # Rate limited, wait longer
                        retry_after = float(response.headers.get("Retry-After", "60"))
                        logger.warning(f"{self._provider} rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    elif response.status_code >= 500:
                        # Server error, retry with backoff
                        raise APIScorerError(
                            f"Server error: {response.status_code}",
                            self._provider,
                            response.status_code,
                        )

                    else:
                        # Client error, don't retry
                        raise APIScorerError(
                            f"Client error: {response.status_code} - {response.text}",
                            self._provider,
                            response.status_code,
                        )

            except httpx.TimeoutException:
                last_error = APIScorerError(
                    f"Request timeout after {self._timeout}s",
                    self._provider,
                )

            except httpx.RequestError as e:
                last_error = APIScorerError(
                    f"Request error: {e}",
                    self._provider,
                )

            except APIScorerError:
                raise

            except Exception as e:
                last_error = APIScorerError(
                    f"Unexpected error: {e}",
                    self._provider,
                )

            # Exponential backoff before retry
            if attempt < self._max_retries - 1:
                backoff = (2**attempt) * 1.0  # 1s, 2s, 4s
                logger.warning(
                    f"{self._provider} API call failed, retrying in {backoff}s "
                    f"(attempt {attempt + 1}/{self._max_retries})"
                )
                await asyncio.sleep(backoff)

        raise last_error or APIScorerError(
            "Max retries exceeded",
            self._provider,
        )

    def compute_scores(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute relevance scores synchronously.

        Note: This is a sync wrapper around async implementation.
        For async usage, use compute_scores_async.

        Args:
            query: Query string.
            documents: Document list.

        Returns:
            NumPy array of scores.
        """
        return asyncio.run(self.compute_scores_async(query, documents))

    async def compute_scores_async(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute relevance scores asynchronously.

        Args:
            query: Query string.
            documents: Document list.

        Returns:
            NumPy array of scores.
        """
        if not documents:
            return np.array([], dtype=np.float32)

        try:
            scores = await self._make_request(query, documents)
            return np.array(scores, dtype=np.float32)

        except APIScorerError as e:
            logger.error(f"API scorer error ({e.provider}): {e}")
            raise

    def get_config(self) -> dict[str, Any]:
        """Get scorer configuration."""
        return {
            "name": self.name,
            "provider": self._provider,
            "model": self._model,
            "base_url": self._base_url,
            "timeout": self._timeout,
            "max_retries": self._max_retries,
            "rate_limit_per_minute": self._rate_limiter.requests_per_minute,
        }


class CohereScorer(APIScorer):
    """Cohere rerank API scorer.

    API Documentation: https://docs.cohere.com/reference/rerank
    """

    def __init__(
        self,
        api_key: str,
        model: str = "rerank-english-v3.0",
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_per_minute: int = 100,
    ):
        """Initialize Cohere scorer.

        Args:
            api_key: Cohere API key.
            model: Model name (default: rerank-english-v3.0).
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            rate_limit_per_minute: Rate limit for API calls.
        """
        super().__init__(
            provider="cohere",
            api_key=api_key,
            base_url="https://api.cohere.ai/v1",
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_per_minute=rate_limit_per_minute,
        )

    @property
    def provider(self) -> str:
        return "cohere"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_request_body(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._model,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            body["top_n"] = top_n
        return body

    def _parse_response(self, response: dict[str, Any]) -> list[float]:
        """Parse Cohere rerank response.

        Response format:
        {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 2, "relevance_score": 0.87},
                ...
            ]
        }
        """
        results = response.get("results", [])
        # Cohere returns results sorted by score, with original indices
        # We need to map back to original document order
        scores = [0.0] * len(results)
        for result in results:
            idx = result.get("index", 0)
            score = result.get("relevance_score", 0.0)
            if idx < len(scores):
                scores[idx] = score
        return scores


class JinaScorer(APIScorer):
    """Jina rerank API scorer.

    API Documentation: https://api.jina.ai/redoc#tag/rerank
    """

    def __init__(
        self,
        api_key: str,
        model: str = "jina-reranker-v2-base-multilingual",
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_per_minute: int = 100,
    ):
        """Initialize Jina scorer.

        Args:
            api_key: Jina API key.
            model: Model name (default: jina-reranker-v2-base-multilingual).
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
            rate_limit_per_minute: Rate limit for API calls.
        """
        super().__init__(
            provider="jina",
            api_key=api_key,
            base_url="https://api.jina.ai/v1",
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit_per_minute=rate_limit_per_minute,
        )

    @property
    def provider(self) -> str:
        return "jina"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_request_body(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._model,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            body["top_n"] = top_n
        return body

    def _parse_response(self, response: dict[str, Any]) -> list[float]:
        """Parse Jina rerank response.

        Response format similar to Cohere:
        {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 2, "relevance_score": 0.87},
                ...
            ]
        }
        """
        results = response.get("results", [])
        scores = [0.0] * len(results)
        for result in results:
            idx = result.get("index", 0)
            score = result.get("relevance_score", 0.0)
            if idx < len(scores):
                scores[idx] = score
        return scores


# Factory function for creating API scorers
def create_api_scorer(
    provider: str,
    api_key: str,
    model: str | None = None,
    **kwargs: Any,
) -> APIScorer:
    """Create an API scorer based on provider.

    Args:
        provider: Provider name (cohere, jina).
        api_key: API key.
        model: Model name (optional).
        **kwargs: Additional arguments passed to scorer constructor.

    Returns:
        APIScorer instance.

    Raises:
        ValueError: If provider is not supported.
    """
    provider = provider.lower()

    if provider == "cohere":
        return CohereScorer(
            api_key=api_key,
            model=model or "rerank-english-v3.0",
            **kwargs,
        )
    elif provider == "jina":
        return JinaScorer(
            api_key=api_key,
            model=model or "jina-reranker-v2-base-multilingual",
            **kwargs,
        )
    else:
        raise ValueError(f"Unsupported API provider: {provider}. Supported providers: cohere, jina")
