"""RerankEngineAdapter - Backward-compatible adapter for RerankEngine.

This module provides an adapter that wraps RerankEngine as a
BaseRerankProvider, ensuring backward compatibility.

Reference: Docs/20-RerankEngine-Architecture.md Section 6.2
Reference: Docs/25-Rerank-Correction-Plan.md Section 3.2
"""

from __future__ import annotations

from typing import Any

from raghub_mcp.providers.base import ProviderCategory
from raghub_mcp.providers.registry import registry
from raghub_mcp.rerank_engine.models import BackendType

from .api_backend import APIBackendAdapter
from .base import BaseRerankProvider, RerankResult


@registry.register(ProviderCategory.RERANK, "rerank-engine")
class RerankEngineAdapter(BaseRerankProvider):
    """Adapter to wrap RerankEngine as BaseRerankProvider.

    This allows the new RerankEngine to be used through the
    existing BaseRerankProvider interface, maintaining backward
    compatibility with existing code.

    Supports multiple backends:
    - ONNX backend: Local ONNX model inference (via RerankEngine)
    - API backend: External rerank API (via APIBackendAdapter)
    - LOCAL backend: (reserved) Local model service

    Example:
        >>> # ONNX backend
        >>> adapter = RerankEngineAdapter.from_config({
        ...     "backend": "onnx",
        ...     "scorer_type": "onnx",
        ...     "scorer_config": {"model_path": "./model.onnx"},
        ... })
        >>>
        >>> # API backend
        >>> adapter = RerankEngineAdapter.from_config({
        ...     "backend": "api",
        ...     "api_url": "https://api.example.com/v1",
        ...     "api_key": "...",
        ... })
    """

    NAME = "rerank-engine"

    def __init__(self, engine: Any) -> None:
        """Initialize adapter with RerankEngine.

        Args:
            engine: RerankEngine instance to wrap.
        """
        self._engine = engine

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Rerank documents using the wrapped engine.

        Args:
            query: The search query.
            documents: List of document texts.
            top_k: Number of results to return.

        Returns:
            List of RerankResult sorted by score.
        """
        from raghub_mcp.rerank_engine.models import RerankRequest

        # Build request for engine
        request = RerankRequest(
            query=query,
            documents=[{"id": str(i), "text": doc} for i, doc in enumerate(documents)],
            top_k=top_k,
        )

        # Execute rerank
        engine_results = self._engine.rerank(request)

        # Convert to legacy RerankResult format
        return [
            RerankResult(
                index=r.original_index,
                score=r.score,
                text=r.text,
            )
            for r in engine_results
        ]

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> BaseRerankProvider:
        """Create adapter from configuration.

        Routes to appropriate backend based on config:
        - backend="onnx": Uses RerankEngine with ONNX scorer
        - backend="api": Uses APIBackendAdapter directly

        Args:
            config: Configuration dictionary with:
                - backend: Backend type ("onnx", "api", "local")
                - For ONNX backend:
                    - scorer_type: Type of scorer ("onnx", "bm25", "vector", "hybrid")
                    - scorer_config: Scorer configuration
                    - embedding_provider_name: Optional name of embedding provider
                    - rank_strategy: Rank strategy name
                    - post_processors: Post-processor configs
                - For API backend:
                    - api_url: API endpoint URL
                    - api_key: API key
                    - model: Model name
                    - timeout: Request timeout
                    - max_retries: Max retry attempts

        Returns:
            Configured provider instance (RerankEngineAdapter or APIBackendAdapter).
        """
        from raghub_mcp.rerank_engine.engine import RerankConfig, RerankEngine
        from raghub_mcp.rerank_engine.models import BackendType

        backend = config.get("backend", "onnx")

        # Parse backend type
        if isinstance(backend, str):
            backend = BackendType(backend)

        # API Backend: Return APIBackendAdapter directly
        if backend == BackendType.API:
            return APIBackendAdapter.from_config(config)

        # LOCAL Backend: Reserved for future implementation
        if backend == BackendType.LOCAL:
            raise NotImplementedError(
                "LOCAL backend is reserved for future implementation. "
                "Use 'onnx' or 'api' backend."
            )

        # ONNX Backend: Use RerankEngine
        # Get embedding_provider if configured
        embedding_provider = None
        embedding_provider_name = config.get("embedding_provider_name")

        if embedding_provider_name:
            from raghub_mcp.providers.factory import factory

            embedding_provider = factory.get_embedding_provider(embedding_provider_name)

        engine_config = RerankConfig(
            backend=backend,
            scorer_type=config.get("scorer_type", "onnx"),
            scorer_config=config.get("scorer_config", {}),
            embedding_provider_name=embedding_provider_name,
            embedding_provider=embedding_provider,  # Inject
            rank_strategy=config.get("rank_strategy", "standard"),
            rank_strategy_config=config.get("rank_strategy_config", {}),
            post_processors=config.get("post_processors", []),
        )

        engine = RerankEngine(engine_config)
        return cls(engine)