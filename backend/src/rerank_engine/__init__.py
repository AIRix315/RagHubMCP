"""RerankEngine - Composable reranking for RAG pipelines.

This module provides the core reranking engine with:
- Pluggable scorers (ONNX, API, Vector)
- Configurable ranking strategies
- Score post-processing pipeline
- Full observability of intermediate states
- Query caching for performance
- Provider fallback for resilience

Reference: Docs/20-RerankEngine-Architecture.md
"""

from .models import (
    RerankContext,
    RerankRequest,
    RerankResult,
    RankStrategyType,
    ScorerType,
)
from .core import BaseScorer, BaseRankStrategy, BasePostProcessor, ScoredDocument
from .cache import QueryCache, get_cache, reset_cache
from .fallback import FallbackManager, get_fallback_manager, reset_fallback_manager

__all__ = [
    # Models
    "RerankRequest",
    "RerankResult",
    "RerankContext",
    "ScorerType",
    "RankStrategyType",
    # Core abstractions
    "BaseScorer",
    "BaseRankStrategy",
    "BasePostProcessor",
    "ScoredDocument",
    # Performance
    "QueryCache",
    "get_cache",
    "reset_cache",
    # Reliability
    "FallbackManager",
    "get_fallback_manager",
    "reset_fallback_manager",
]