"""RerankEngineAdapter - Backward-compatible adapter for RerankEngine.

This module provides an adapter that wraps RerankEngine as a
BaseRerankProvider, ensuring backward compatibility.

Reference: Docs/20-RerankEngine-Architecture.md Section 6.2
"""

from __future__ import annotations

from typing import Any

from .base import BaseRerankProvider, RerankResult


class RerankEngineAdapter(BaseRerankProvider):
    """Adapter to wrap RerankEngine as BaseRerankProvider.

    This allows the new RerankEngine to be used through the
    existing BaseRerankProvider interface, maintaining backward
    compatibility with existing code.

    Example:
        >>> from rerank_engine.engine import RerankEngine, RerankConfig
        >>> config = RerankConfig(scorer_type="onnx", ...)
        >>> engine = RerankEngine(config)
        >>> adapter = RerankEngineAdapter(engine)
        >>> # Now use adapter as BaseRerankProvider
        >>> results = adapter.rerank("query", ["doc1", "doc2"])
    """

    NAME = "rerank_engine"

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
        from rerank_engine.models import RerankRequest

        # Build request for engine
        request = RerankRequest(
            query=query,
            documents=[
                {"id": str(i), "text": doc}
                for i, doc in enumerate(documents)
            ],
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
    def from_config(cls, config: dict[str, Any]) -> RerankEngineAdapter:
        """Create adapter from configuration.

        Args:
            config: Configuration dictionary with:
                - scorer_type: Type of scorer
                - scorer_config: Scorer configuration
                - rank_strategy: Rank strategy name
                - rank_strategy_config: Rank strategy configuration
                - post_processors: List of post-processor configs

        Returns:
            Configured RerankEngineAdapter instance.
        """
        from rerank_engine.engine import RerankConfig, RerankEngine

        engine_config = RerankConfig(
            scorer_type=config.get("scorer_type", "onnx"),
            scorer_config=config.get("scorer_config", {}),
            rank_strategy=config.get("rank_strategy", "standard"),
            rank_strategy_config=config.get("rank_strategy_config", {}),
            post_processors=config.get("post_processors", []),
        )

        engine = RerankEngine(engine_config)
        return cls(engine)