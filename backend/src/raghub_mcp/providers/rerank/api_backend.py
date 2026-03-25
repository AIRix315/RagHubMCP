"""API Backend Adapter for external rerank services.

This adapter calls external rerank APIs that return pre-ranked results,
unlike ONNX scorer which returns scores that need ranking.

The key difference from ONNX backend:
- ONNX: query + docs -> scores[] -> PostProcessor -> RankStrategy -> results
- API:  query + docs -> pre-ranked results -> optionally PostProcessor -> results

Reference: Docs/25-Rerank-Correction-Plan.md Section 3.1
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .base import BaseRerankProvider, RerankResult

logger = logging.getLogger(__name__)


class APIBackendAdapter(BaseRerankProvider):
    """Adapter for external Rerank API services.

    Calls user-configured API endpoints that return ranked results.
    The API returns sorted documents with relevance scores, not raw scores.

    Attributes:
        api_url: User's rerank API endpoint URL
        api_key: Optional API key for authentication
        model: Optional model name (some APIs require this)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
    """

    NAME = "api-backend"

    def __init__(
        self,
        api_url: str,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize API Backend Adapter.

        Args:
            api_url: API endpoint URL (required)
            api_key: Optional API key for authentication
            model: Optional model name for APIs that require it
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def api_url(self) -> str:
        """Get API URL."""
        return self._api_url

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Call API and return ranked results.

        Args:
            query: The search query
            documents: List of document texts to rerank
            top_k: Number of results to return

        Returns:
            List of RerankResult sorted by score (descending).
        """
        return asyncio.run(self._rerank_async(query, documents, top_k))

    async def _rerank_async(
        self,
        query: str,
        documents: list[str],
        top_k: int,
    ) -> list[RerankResult]:
        """Async implementation of rerank."""
        if not documents:
            return []

        # Build request body - standard rerank API format
        request_body: dict[str, Any] = {
            "query": query,
            "documents": documents,
            "top_n": min(top_k, len(documents)),
        }
        if self._model:
            request_body["model"] = self._model

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # Make request with retry
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        f"{self._api_url}/rerank",
                        json=request_body,
                        headers=headers,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_response(data, documents)

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", "5"))
                        await asyncio.sleep(retry_after)
                        continue

                    # Client error - don't retry
                    if 400 <= response.status_code < 500:
                        raise RuntimeError(
                            f"API error {response.status_code}: {response.text}"
                        )

                    # Server error - retry with backoff
                    last_error = RuntimeError(f"Server error {response.status_code}")

            except httpx.TimeoutException:
                last_error = RuntimeError(f"Request timeout after {self._timeout}s")
            except httpx.RequestError as e:
                last_error = RuntimeError(f"Request failed: {e}")

            # Exponential backoff
            if attempt < self._max_retries - 1:
                await asyncio.sleep(2**attempt)

        raise last_error or RuntimeError("Max retries exceeded")

    def _parse_response(
        self,
        response: dict[str, Any],
        original_documents: list[str],
    ) -> list[RerankResult]:
        """Parse API response into RerankResult format.

        Supports multiple response formats from different API providers:
        - Cohere: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
        - Jina: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
        - Jina Score: {"data": [{"score": 0.95}, ...]}
        - Custom: {"results": [{"id": "0", "text": "...", "relevance_score": 0.95}, ...]}

        Args:
            response: API response dictionary
            original_documents: Original document texts for fallback

        Returns:
            List of RerankResult sorted by score.
        """
        # Handle 'data' key (Jina Score API)
        results_data = response.get("results", response.get("data", []))
        results: list[RerankResult] = []

        for item in results_data:
            # Get index - support both "index" and "id" field names
            idx = item.get("index")
            if idx is None:
                # Some APIs use "id" as string
                id_val = item.get("id", "0")
                try:
                    idx = int(id_val) if isinstance(id_val, str) else id_val
                except (ValueError, TypeError):
                    idx = 0

            # Get score - support various field names
            score = item.get("relevance_score") or item.get("score", 0.0)

            # Get text - may be returned or use original
            text = item.get("text") or (
                original_documents[idx] if idx < len(original_documents) else ""
            )

            results.append(
                RerankResult(
                    index=idx,
                    score=float(score),
                    text=text,
                )
            )

        # Sort by score descending (API may already return sorted, but ensure)
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "APIBackendAdapter":
        """Create instance from configuration.

        Args:
            config: Configuration dict with:
                - api_url: Required API endpoint URL
                - api_key: Optional API key
                - model: Optional model name
                - timeout: Optional timeout (default 30s)
                - max_retries: Optional retry count (default 3)

        Returns:
            Configured APIBackendAdapter instance.
        """
        return cls(
            api_url=config["api_url"],
            api_key=config.get("api_key"),
            model=config.get("model"),
            timeout=config.get("timeout", 30.0),
            max_retries=config.get("max_retries", 3),
        )